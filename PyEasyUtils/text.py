import re
import string
import random
import unicodedata
import json
import polars
import urllib.parse as urlparse
from typing import Optional

#############################################################################################################

def rawString(
    text: str
):
    """
    Return as raw string representation of text
    """
    RawMap = {
        7: r'\a',
        8: r'\b',
        9: r'\t',
        10: r'\n',
        11: r'\v',
        12: r'\f',
        13: r'\r'
    }
    text = r''.join([RawMap.get(ord(Char), Char) for Char in text])
    '''
    StringRepresentation = repr(text)[1:-1] #StringRepresentation = text.encode('unicode_escape').decode()
    return re.sub(r'\\+', lambda arg: r'\\', StringRepresentation).replace(r'\\', '\\').replace(r'\'', '\'') #return eval("'%s'" % canonical_string)
    '''
    return unicodedata.normalize('NFKC', text)

#############################################################################################################

def findURL(
    string: str
):
    """
    Function to find URL in a string
    """
    URLList = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|(?:%[0-9a-fA-F][0-9a-fA-F])|[!*\\(\\),])+').findall(rawString(string))
    return URLList[0] if URLList.__len__() < 2 else URLList


def makeSafeForURL(string):
    return urlparse.quote(
        string = str(string),
        safe = ':,[]'
    )


def isURL(content: str):
    """
    Check if content is a url
    """
    if urlparse.urlparse(content).scheme in ['http', 'https']:
        return True
    else:
        return False

#############################################################################################################

def isJson(content: str):
    """
    Check if content is a json
    """
    try:
        json.loads(json.dumps(eval(content)))
        return True
    except:
        return False

#############################################################################################################

def generateRandomString(
    amount: int = 9
):
    randomString = ''.join(
        random.sample(
            string.ascii_letters + string.digits,
            k = amount
        )
    )
    return randomString

#############################################################################################################

@polars.Config( 
    tbl_formatting = "ASCII_MARKDOWN",        
    tbl_hide_column_data_types = True,
    tbl_hide_dataframe_shape = True,
)
def _toMarkdown(df: polars.DataFrame) -> str:
    return str(df)


def toMarkdown(content: str):
    """
    Convert content to markdown
    """
    if isURL(content):
        content = f"[URL]({content})"
    if isJson(content):
        content = _toMarkdown(polars.DataFrame(json.loads(json.dumps(eval(content)))))
    return content

#############################################################################################################

class richTextManager:
    """
    Manage rich text
    """
    def __init__(self):
        self.richTextLines = []

    def _toHtml(self, text, align, size, weight, letterSpacing, lineHeight):
        Style = f"'text-align:{align}; font-size:{size}pt; font-weight:{weight}; letter-spacing: {letterSpacing}px; line-height: {lineHeight}px'"
        content = re.sub(
            pattern = "[\n]",
            repl = "<br>",
            string = text
        ) if text is not None else None
        return f"<p style={Style}>{content}</p>" if content is not None else ''

    def addTitle(self,
        text: Optional[str] = None,
        align: str = "left",
        size: float = 12.3,
        weight: float = 630.,
        spacing: float = 0.9,
        lineHeight: float = 24.6,
    ):
        head = f"<body>{self._toHtml(text, align, size, weight, spacing, lineHeight)}</body>" #head = f"<head><title>{self._toHtml(text, align, size, weight, spacing, lineHeight)}</title></head>"
        self.richTextLines.append(head)
        return self

    def addBody(self,
        text: Optional[str] = None,
        align: str = "left",
        size: float = 9.3,
        weight: float = 420.,
        spacing: float = 0.6,
        lineHeight: float = 22.2,
    ):
        body = f"<body>{self._toHtml(text, align, size, weight, spacing, lineHeight)}</body>"
        self.richTextLines.append(body)
        return self

    def richText(self):
        richText = "<html>\n%s\n</html>" % '\n'.join(self.richTextLines)
        return (richText)


def setRichText(
    text: str = "",
    align: str = "left",
    size: float = 9.6,
    weight: float = 450.,
    spacing: float = 0.66,
    lineHeight: float = 22.2,
):
    """
    Function to set rich text
    """
    return richTextManager().addBody(text, align, size, weight, spacing, lineHeight).richText()

#############################################################################################################