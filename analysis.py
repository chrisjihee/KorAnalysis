# 공통 모듈 임포트
from pathlib import Path
import json

# API 인증키 설정
my_access_key = "8541da0b-c49c-47ce-9652-aaad6c580997"

# API 호출 함수 정의
import urllib3


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


# 단순 텍스트 분석
response = analyze_by_openapi(text="대한민국은 동아시아의 한반도 군사 분계선 남부에 위치한 국가이다.", key=my_access_key)
response_code = response.status
response_data = response.data.decode("utf-8")
print("-" * 120)
print("[response_code] " + str(response_code))
print("[response_data]\n" + response_data)
print("-" * 120)

# 응답 문자열 -> JSON -> 파일 저장
object_origin = json.loads(response_data)
json_origin = json.dumps(object_origin, ensure_ascii=False, indent=4)

Path("out").mkdir(exist_ok=True)
Path("out/origin.json").write_text(json_origin)

# 필요 데이터클래스 정의
from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin


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


# 파일 로드 -> JSON -> 데이터클래스(객체)
json_read = Path("out/origin.json").read_text()
custom = Response.from_json(json_read)
json_custom = custom.to_json(indent=4, ensure_ascii=False)

# JSON 문자열 비교
print("json_read == json_origin:", json_read == json_origin)
print("json_custom == json_origin:", json_custom == json_origin)

# 데이터클래스(객체) -> JSON -> 파일 저장
Path("out").mkdir(exist_ok=True)
Path("out/custom.json").write_text(json_custom)


# 파일 목록 조회 함수 정의
def list_files(path: str, ext: str = "*") -> list[Path]:
    return sorted(Path(path).glob(f"*.{ext}"))


# 파일 목록 출력 테스트
print("* Data files:")
for file in list_files("data"):
    print("  + " + str(file))

# 카운터 초기화
from collections import Counter

nouns = Counter()
verbs = Counter()
nes = Counter()
noun_tags = ("NNP", "NNG", "SL")
verb_tabs = ("VV", "VA")


# 개체명 변환 함수
def upper_ne_type(x: str) -> str:
    return x.split('_')[0]


# 파일별 분석하기 수행
print("* Data files:")
for file in list_files("data"):
    # 파일명 출력
    print("  + " + str(file))
    # 파일 내용을 OpenAPI로 분석
    res = analyze_by_openapi(text=file.read_text(), key=my_access_key)
    obj = Response.from_json(res.data.decode("utf-8"))
    # 분석 결과 처리
    if obj.return_object is not None:
        doc: Document = obj.return_object
        # 문장별 처리
        for sentence in doc.sentence:
            # 문장 텍스트 출력
            print("    - " + sentence.text.strip())
            # 어휘의미(WSD) 단위별 처리
            for wsd in sentence.WSD:
                if wsd.type in noun_tags:
                    nouns[wsd.text] += 1
                elif wsd.type in verb_tabs:
                    verbs[wsd.text + "다"] += 1
            # 개체명(NE) 단위별 처리
            for ne in sentence.NE:
                nes[f"{ne.text}/{upper_ne_type(ne.type)}"] += 1

# 고빈도 명사 출력
print(nouns.most_common(50))
# 고빈도 동사 출력
print(verbs.most_common(50))
# 고빈도 개체명 출력
print(nes.most_common(50))

# 워드클라우드 생성 함수 정의
from wordcloud import WordCloud


def make_wordcloud(cnt: Counter,
                   font_path="font/NanumSquareB.ttf",
                   background_color="white",
                   max_font_size=240,
                   width=800, height=600):
    wc = WordCloud(font_path=font_path, background_color=background_color, max_font_size=max_font_size, width=width, height=height)
    wc.generate_from_frequencies(dict(cnt))
    return wc


# 워드클라우드 생성하여 파일로 저장
Path("out").mkdir(exist_ok=True)
noun_wc = make_wordcloud(nouns)
verb_wc = make_wordcloud(verbs)
ne_wc = make_wordcloud(nes)
noun_wc.to_file("out/noun.png")
verb_wc.to_file("out/verb.png")
ne_wc.to_file("out/ne.png")

# Figure 생성 함수 정의
import matplotlib.pyplot as plt


def make_figure(wc: WordCloud, show: bool = False):
    plt.figure(figsize=(10, 8))
    plt.axis('off')
    plt.imshow(wc)
    if show:
        plt.show()


make_figure(noun_wc, show=True)
make_figure(verb_wc, show=True)
make_figure(ne_wc, show=True)
