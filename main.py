import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import urllib3
from dataclasses_json import DataClassJsonMixin

my_access_key = "8541da0b-c49c-47ce-9652-aaad6c580997"


def analyze_by_openapi(text: str,
                       key: str,
                       url: str = "http://aiopen.etri.re.kr:8000/WiseNLU"):
    req = {
        "argument": {
            "analysis_code": "ner",
            "text": text,
        }
    }
    http = urllib3.PoolManager()
    res = http.request(
        method="POST",
        url=url,
        headers={"Content-Type": "application/json; charset=UTF-8", "Authorization": key},
        body=json.dumps(req)
    )
    return res


response = analyze_by_openapi(text="대한민국은 동아시아의 한반도 군사 분계선 남부에 위치한 국가이다.", key=my_access_key)
response_code = response.status
response_data = response.data.decode("utf-8")
print("-" * 120)
print("[response_code] " + str(response_code))
print("[response_data]\n" + response_data)
print("-" * 120)

object_origin = json.loads(response_data)
json_origin = json.dumps(object_origin, ensure_ascii=False, indent=4)

Path("out").mkdir(exist_ok=True)
Path("out/origin.json").write_text(json_origin)


@dataclass
class Morp(DataClassJsonMixin):
    id: int
    lemma: str
    type: str
    position: int


@dataclass
class WSD(DataClassJsonMixin):
    id: int
    text: str
    type: str
    scode: str
    begin: int
    end: int


@dataclass
class NE(DataClassJsonMixin):
    id: int
    text: str
    type: str
    begin: int
    end: int


@dataclass
class Word(DataClassJsonMixin):
    id: int
    text: str
    begin: int
    end: int


@dataclass
class Sentence(DataClassJsonMixin):
    id: int
    text: str
    word: list[Word]
    morp: list[Morp]
    WSD: list[WSD]
    NE: list[NE]


@dataclass
class Document(DataClassJsonMixin):
    doc_id: str
    sentence: list[Sentence]


@dataclass
class Response(DataClassJsonMixin):
    result: int
    reason: str | None = None
    return_object: Document | None = None


json_read = Path("out/origin.json").read_text()

custom = Response.from_json(json_read)
json_custom = custom.to_json(indent=4, ensure_ascii=False)

print("json_read == json_origin:", json_read == json_origin)
print("json_custom == json_origin:", json_custom == json_origin)

Path("out").mkdir(exist_ok=True)
Path("out/custom.json").write_text(json_custom)


def list_files(path: str, ext: str = "*") -> list[Path]:
    return sorted(Path(path).glob(f"*.{ext}"))


print("* Data files:")
for file in list_files("data"):
    print("  + " + str(file))

noun_tags = ("NNP", "NNG", "SL")
verb_tabs = ("VV", "VA")
nouns = Counter()
verbs = Counter()
nes = Counter()


def upper_ne_type(x: str) -> str:
    return x.split('_')[0]


print("* Data files:")
for file in list_files("data"):
    print("  + " + str(file))
    res = analyze_by_openapi(text=file.read_text(), key=my_access_key)
    obj = Response.from_json(res.data.decode("utf-8"))
    if obj.return_object is not None:
        doc: Document = obj.return_object
        for sentence in doc.sentence:
            print("    - " + sentence.text.strip())
            for wsd in sentence.WSD:
                if wsd.type in noun_tags:
                    nouns[wsd.text] += 1
                if wsd.type in verb_tabs:
                    verbs[wsd.text + "다"] += 1
            for ne in sentence.NE:
                nes[f"{ne.text}/{upper_ne_type(ne.type)}"] += 1

print(nouns.most_common(50))
print(verbs.most_common(50))
print(nes.most_common(50))

from wordcloud import WordCloud

Path("out").mkdir(exist_ok=True)
wc = WordCloud(font_path="font/NanumSquareB.ttf", background_color="white", max_font_size=240, width=800, height=600)
wc.generate_from_frequencies(dict(nouns)).to_file("out/noun.png")
wc.generate_from_frequencies(dict(verbs)).to_file("out/verb.png")
wc.generate_from_frequencies(dict(nes)).to_file("out/ne.png")

import matplotlib.pyplot as plt

plt.figure(figsize=(10, 8))
plt.axis('off')
plt.imshow(wc.generate_from_frequencies(dict(nouns)))
plt.show()
plt.imshow(wc.generate_from_frequencies(dict(verbs)))
plt.show()
plt.imshow(wc.generate_from_frequencies(dict(nes)))
plt.show()
