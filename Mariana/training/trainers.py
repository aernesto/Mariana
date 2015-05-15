import cPickle, time, sys, traceback, random, types
import numpy
from collections import OrderedDict

from pyGeno.tools.parsers.CSVTools import CSVFile
import theano.tensor as tt

import Mariana.settings as MSET


class EndOfTraining(Exception) :
	"""Exception raised when a training criteria is met"""
	def __init__(self, stopCriterion) :
		self.stopCriterion = stopCriterion
		self.message = "End of training: %s" % stopCriterion.endMessage()

class TrainingRecorder(object):
 	"""docstring for OutputRecorder"""
 	def __init__(self, runName, csvLegend, noBestSets = ("train", )):
		self.runName = runName
		self.csvLegend = csvLegend
		self.noBestSets = noBestSets

 		self.outputLayers = []
		self.bestScores = {}
		self.currentScores = {}
		self.bestFilenames = {}
		self.maps = {}

		self.stackLen = 0
		self.currentLen = 0
		self.stackLen = 0
		self.csvFile = None

		self._mustInit = True

	def addMap(self, mapName, mapValue) :
		if len(mapValue) > 1 :
			self.maps[mapName] = mapValue

	def addOutput(self, outputLayer) :
		self.outputLayers.append(outputLayer)

	def _init(self) :
		for o in self.outputLayers :
			self.bestScores[o.name] = {}
			self.currentScores[o.name] = {}
			self.bestFilenames[o.name] = {}
			for s, v in self.maps.iteritems() :
				self.bestScores[o.name][s] = []
				self.currentScores[o.name][s] = []
				self.bestFilenames[o.name][s] = "best_%s_%s" % (s, o.name)

		self.csvLegend.append("score")
		self.csvLegend.append("best_score")
		self.csvLegend.append("set")
		self.csvLegend.append("output")

		self.csvFile = CSVFile(legend = self.csvLegend)
		self.csvFile.streamToFile("%s-evolution.csv" % (self.runName, ), writeRate = len(self.maps) * (len(self.outputLayers) + 1) ) #(output + avg) x #set

		self._mustInit = False

	def getBestScore(self, outputLayer, theSet) :
		return self.bestScores[outputLayer.name][theSet][-1]

	def getCurrentScore(self, outputLayer, theSet) :
		return self.currentScores[outputLayer.name][theSet][-1]

	def getAverageBestScore(self, theSet) :
		l = []
		for o in self.outputLayers :
			l.append(self.bestScores[o.name][theSet][-1])
		return numpy.mean(l)

	def getAverageCurrentScore(self, theSet) :
		l = []
		for o in self.outputLayers :
			l.append(self.currentScores[o.name][theSet][-1])
		return numpy.mean(l)

	def commitToCSVs(self, **csvValues) :
		"""saves the stack to disk. It will automatically add the scores and the sets to the file"""
		def _fillLine(csvFile, score, bestScore, setName, setLen, outputName, **csvValues) :
			line = csvFile.newLine()
			for k, v in csvValues.iteritems() :
				line[k] = v
			line["score"] = score
			line["best_score"] = bestScore
			line["set"] = "%s(%s)" %(setName, setLen)
			line["output"] = outputName
			line.commit()
		
		if self._mustInit :
			self._init()

		start = self.currentLen - self.stackLen
		stop = self.currentLen
		for i in xrange(start, stop) :
			for theSet in self.maps :
				meanCurrent = []
				meanBest = []
				for o in self.outputLayers :
					score = None
					if theSet not in self.noBestSets :
						try :
							bestScore = self.bestScores[o.name][theSet][i]
						except IndexError :
							bestScore = self.bestScores[o.name][theSet][-1]
					else :
						bestScore = self.currentScores[o.name][theSet][i]

					score = self.currentScores[o.name][theSet][i]
					_fillLine( self.csvFile, score, bestScore, theSet, len(self.maps[theSet]), o.name, **csvValues)

					meanCurrent.append(score)
					meanBest.append(bestScore)
			
				_fillLine( self.csvFile, numpy.mean(meanCurrent), numpy.mean(meanBest), theSet, len(self.maps[theSet]), "average", **csvValues)
		
		self.stackLen = 0

	def newEntry(self) :
		self.stackLen += 1
		self.currentLen += 1 

	def updateScore(self, outputLayerName, theSet, score) :
		if self._mustInit :
			self._init()

		self.currentScores[outputLayerName][theSet].append(score)
		if theSet not in self.noBestSets :
			if len(self.bestScores[outputLayerName][theSet]) > 1 :
				if (score < self.bestScores[outputLayerName][theSet][-1] ) :
					self.bestScores[outputLayerName][theSet].append(score)
			else :
				self.bestScores[outputLayerName][theSet].append(score)

	def printCurrentState(self) :
		if self.currentLen > 0 :
			print "\n=M=>State %s:" % self.currentLen
			for s in self.maps :
				print "  |-%s set" % s
				for o in self.outputLayers :
					if s not in self.noBestSets and self.currentScores[o.name][s][-1] == self.bestScores[o.name][s][-1] :
						highlight = "+best+"
					elif len(self.bestScores[o.name][s]) > 0 :
						highlight = "(best: %s)" % (self.bestScores[o.name][s][-1])
					else :
						highlight = ""

					print "    |->%s: %s %s" % (o.name, self.currentScores[o.name][s][-1], highlight)
		else :
			print "=M=> Nothing to show yet"

class DefaultTrainer(object):
	"""Should serve for most purposes"""
	def __init__(self, trainMaps, testMaps, validationMaps, trainMiniBatchSize, stopCriteria, testMiniBatchSize = "all", testFrequency = 1, saveOnException = True) :
		
		self.maps = {}
		self.maps["train"] = trainMaps
		self.maps["test"] = testMaps
		self.maps["validation"] = validationMaps
		
		self.miniBatchSizes = {
			"train" : trainMiniBatchSize,
			"test" : testMiniBatchSize,
			"validation" : testMiniBatchSize
		}

		self.stopCriteria = stopCriteria
		
		self.testFrequency = testFrequency
		
		self.saveOnException = saveOnException
		
		self.reset()

	def reset(self) :
		'resets the beast'	
		
		self.recorder = None
		self.currentEpoch = 0

	def getBestValidationModel(self) :
		"""loads the best validation model from disk and returns it"""
		f = open(self.bestValidationModelFile + ".mariana.pkl")
		model = cPickle.load(f) 
		f.close()
		return model

	def getBestTestModel(self) :
		"""loads the best Test model from disk and returns it"""
		f = open(self.bestTestModelFile + ".mariana.pkl")
		model = cPickle.load(f)
		f.close()
		return model
		
	def start(self, name, model, *args, **kwargs) :
		"""Starts the training. If anything bad and unexpected happens during training, the Trainer
		will attempt to save the model and logs."""

		def _dieGracefully() :
			exType, ex, tb = sys.exc_info()
			# traceback.print_tb(tb)
			death_time = time.ctime().replace(' ', '_')
			filename = "dx-xb_" + name + "_death_by_" + exType.__name__ + "_" + death_time
			sys.stderr.write("\n===\nDying gracefully from %s, and saving myself to:\n...%s\n===\n" % (exType, filename))
			model.save(filename)
			f = open(filename +  ".traceback.log", 'w')
			f.write("Mariana training Interruption\n=============================\n")
			f.write("\nDetails\n-------\n")
			f.write("Name: %s\n" % name)
			f.write("Killed by: %s\n" % str(exType))
			f.write("Time of death: %s\n" % death_time)
			f.write("Model saved to: %s\n" % filename)
			f.write("\nTraceback\n---------\n")

			f.write(str(traceback.extract_tb(tb)).replace("), (", "),\n(").replace("[(","[\n(").replace(")]",")\n]"))
			f.flush()
			f.close()

		self.currentEpoch = 0

		if not self.saveOnException :
			return self._run(name, model, *args, **kwargs)
		else :
			try :
				return self._run(name, model, *args, **kwargs)
			except EndOfTraining as e :
				print e.message
				death_time = time.ctime().replace(' ', '_')
				filename = "finished_" + name +  "_" + death_time
				f = open(filename +  ".stopreason.txt", 'w')
				f.write("Time of death: %s\n" % death_time)
				f.write("Epoch of death: %s\n" % self.currentEpoch)
				f.write("Stopped by: %s\n" % e.stopCriterion.name)
				f.write("Reason: %s\n" % e.message)
				f.flush()
				f.close()
				model.save(filename)
			except KeyboardInterrupt :
				_dieGracefully()
				raise
			except :
				_dieGracefully()
				raise

	def _run(self, name, model, reset = True, shuffleMinibatches = True, datasetName = "") :
		
		def setHPs(layer, thing, dct) :
			try :
				thingObj = getattr(l, thing)
			except AttributeError :
				return

			if thingObj is not None :
				if type(thingObj) is types.ListType :
					for obj in thingObj :
						if len(obj.hyperParameters) == 0 :
							dct["%s_%s_%s" % (l.name, thing, obj.name)] = 1
						else :
							for hp in obj.hyperParameters :
								dct["%s_%s_%s_%s" % (l.name, thing, obj.name, hp)] = getattr(obj, hp)
				else :
					if len(thingObj.hyperParameters) == 0 :
						dct["%s_%s" % (l.name, thingObj.name)] = 1
					else :
						for hp in thingObj.hyperParameters :
							dct["%s_%s" % (l.name, hp)] = getattr(thingObj, hp)

		if reset :
			self.reset()
		
		legend = ["name", "epoch", "runtime(min)", "dataset_name"]
		layersForLegend = OrderedDict()
		for l in model.layers.itervalues() :
			layersForLegend["%s_size" % l.name] = len(l)
			try :
				layersForLegend["activation"] = l.activation.__name__
			except AttributeError :
				pass
			setHPs(l, "learningScenario", layersForLegend)
			setHPs(l, "decorators", layersForLegend)
			if l.type == MSET.TYPE_OUTPUT_LAYER :
				setHPs(l, "costObject", layersForLegend)

		legend.extend(layersForLegend.keys())

		self.recorder = TrainingRecorder( name, legend )
		
		for m in self.maps :
			self.recorder.addMap( m, self.maps[m] )

		for l in model.outputs.itervalues() :
			self.recorder.addOutput(l)
		
		print "learning..."
		startTime = time.time()
		self.currentEpoch = 0

		while True :
			self.recorder.newEntry()
		
			for mapName in ["train", "test", "validation"] :		
				aMap = self.maps[mapName]
				if len(aMap) > 0 :
					if self.miniBatchSizes[mapName] == "all" :
						for outputName in aMap.getOutputNames() :
							batchData = aMap.getAll()
							kwargs = batchData[0] #inputs
							kwargs.update({ "target" : batchData[1][outputName]} )
							if mapName == "train" :
								res = model.train(outputName, **kwargs)
							else :
								res = model.test(outputName, **kwargs)
							self.recorder.updateScore(outputName, mapName, res[0])
					else :
						if shuffleMinibatches :
							aMap.shuffle()
						vals = {}
						for i in xrange(0, len(aMap), self.miniBatchSizes[mapName]) :
							batchData = aMap.getBatches(i, self.miniBatchSizes[mapName])
							kwargs = batchData[0] #inputs
							for outputName in aMap.getOutputNames() :
								kwargs.update({ "target" : batchData[1][outputName]} )
								if mapName == "train" :
									res = model.train(outputName, **kwargs)
								else :
									res = model.test(outputName, **kwargs)
								try :
									vals[outputName].append(res[0])
								except KeyError:
									vals[outputName] = [res[0]]

						for outputName in vals :
							self.recorder.updateScore(outputName, mapName, numpy.mean(vals[outputName]))

			runtime = (time.time() - startTime)/60
			
			csvValues = {
				"name" : name,
				"epoch" : self.currentEpoch,
				"runtime(min)" : runtime,
				"dataset_name" : datasetName,
			}
			csvValues.update(layersForLegend)
	
			self.recorder.commitToCSVs(**csvValues)
			self.recorder.printCurrentState()
			sys.stdout.flush()

			for crit in self.stopCriteria :
				if crit.stop(self) :
					raise EndOfTraining(crit)

			self.currentEpoch += 1