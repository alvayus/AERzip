__version__ = "0.8.0"

from .CompressedFileHeader import CompressedFileHeader
from .compressionFunctions import compressDataFromStoredNASFile, extractDataFromCompressedFile, bytesToCompressedFile, compressedFileToBytes, spikesFileToCompressedFile, compressedFileToSpikesFile, extractCompressedData, compressData, decompressData, getCompressedFile, storeFile, checkFileExists, loadFile
from .conversionFunctions import bytesToSpikesFile, spikesFileToBytes, calcRequiredBytes, constructStruct

__all__ = ["CompressedFileHeader", 
           "compressDataFromStoredNASFile", "extractDataFromCompressedFile", "bytesToCompressedFile", "compressedFileToBytes", "spikesFileToCompressedFile", "compressedFileToSpikesFile", "extractCompressedData", "compressData", "decompressData", "getCompressedFile", "storeFile", "checkFileExists", "loadFile",
           "bytesToSpikesFile", "spikesFileToBytes", "calcRequiredBytes", "constructStruct"]
