from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
import pdfminer

from operator import attrgetter


class pdfLine:
    def __init__(self, text, yPos):
        self.text = text
        self.yPos = yPos


class pdfPositionHandling:

    def parse_obj(self, lt_objs, arr, yOffset, minX=150, minY=0):

        # loop over the object list
        for obj in lt_objs:

            if isinstance(obj, pdfminer.layout.LTTextLine) and obj.bbox[0] >= minX and obj.bbox[1] >= minY:
                l = pdfLine(obj.get_text(), obj.bbox[1]+yOffset)
                arr.append(l)

            # if it's a textbox, also recurse
            if isinstance(obj, pdfminer.layout.LTTextBoxHorizontal):
                arr = self.parse_obj(obj._objs, arr, yOffset)

            # if it's a container, recurse
            elif isinstance(obj, pdfminer.layout.LTFigure):
                arr = self.parse_obj(obj._objs, arr, yOffset)

        return arr

    def parsepdf(self, filename, startpage=0, endpage=10000):

        # Open a PDF file.
        fp = open(filename, 'rb')

        # Create a PDF parser object associated with the file object.
        parser = PDFParser(fp)

        # Create a PDF document object that stores the document structure.
        # Password for initialization as 2nd parameter
        document = PDFDocument(parser)

        # Check if the document allows text extraction. If not, abort.
        if not document.is_extractable:
            raise PDFTextExtractionNotAllowed

        # Create a PDF resource manager object that stores shared resources.
        rsrcmgr = PDFResourceManager()

        # Create a PDF device object.
        device = PDFDevice(rsrcmgr)

        # BEGIN LAYOUT ANALYSIS
        # Set parameters for analysis.
        laparams = LAParams()

        # Create a PDF page aggregator object.
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)

        # Create a PDF interpreter object.
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        arr = []
        i = 0
        # loop over all pages in the document
        for page in PDFPage.create_pages(document):
            if i >= startpage and i <= endpage:
                # read the page into a layout object
                interpreter.process_page(page)
                layout = device.get_result()

                # extract text from this object
                arr = self.parse_obj(layout._objs, arr, -i*100000)
            i += 1

        arr.sort(key=lambda x: x.yPos, reverse=True)

        if (arr == None):
            return ""
        return " ".join(map(lambda x: x.text, arr))
