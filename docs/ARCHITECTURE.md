# Architecture

## 시스템 개요

이 저장소는 Railway에 배포된 n8n 인스턴스에서 운영 중인 개인/리서치 자동화 워크플로우를 관리한다. 현재 운영 대상은 텔레그램 메시지를 Obsidian 노트로 저장하는 수집 자동화, 경제/금융 뉴스를 선별해 텔레그램 채널로 발행하는 뉴스 브리핑 자동화, 연합인포맥스 경제지표 기사를 파싱해 Google Sheets와 차트로 축적하는 경제지표 차트 자동화다.

전체 시스템은 세 가지 문제를 해결한다.

- 텔레그램으로 들어오는 텍스트, 사진, 영상 썸네일, 문서를 Obsidian vault에 Markdown 자료로 저장한다.
- 국내외 경제 뉴스를 정규화, 중복 제거, AI 분류/요약한 뒤 매일 아침 텔레그램 브리핑으로 발행한다.
- 환율, 유가, 국고채 관련 기사를 구조화 데이터로 누적하고 최근 60일 차트를 생성해 텔레그램에 공유한다.

운영 인스턴스는 `https://primary-production-90c7.up.railway.app`이며, 워크플로우 정의는 프로젝트별 `projects/*/workflows/*.json` 파일에 보관한다.

## 운영 워크플로우

| 워크플로우 | ID | 상태 | 주요 출력 |
| --- | --- | --- | --- |
| Telegram to Obsidian | `a5RvxdkYFp9VLw5A` | active | OneDrive의 Obsidian vault 내 Markdown/첨부파일, 저장 완료 텔레그램 응답 |
| 뉴스 브리핑 자동화 | `OeA3kgv0CnS2gsZ3` | active | `@undergroundresearch36` 텔레그램 브리핑, Google Sheets 뉴스 아카이브 |
| 경제지표 차트 자동화 | `WW51yZ7oEmyp01kW` | active | Google Sheets 지표 시계열, QuickChart 이미지, 텔레그램 코멘트 |

## 데이터 흐름

### Telegram to Obsidian

트리거는 `Telegram Trigger` 노드다. 사용자가 텔레그램 봇에 메시지를 보내면 `Prepare Message` 코드 노드가 메시지 타입, 첨부파일 ID, 파일명, KST 날짜, 본문 텍스트를 표준 필드로 정리한다.

첨부파일이 있으면 `Check Attachment` 이후 `Get File Info`와 `Download File`이 Telegram Bot API로 파일 경로와 바이너리를 가져오고, `Upload Attachment`가 Microsoft Graph API로 OneDrive의 Obsidian vault 하위 `Telegram/attachments/` 경로에 저장한다. 텍스트 메타데이터는 `generate body`에서 OpenAI `chat/completions` 요청 본문으로 만들어지고, `Generate tag and title`이 `gpt-4o-mini`와 `response_format: json_schema`로 제목과 태그를 생성한다.

첨부파일 처리 결과와 AI 메타데이터는 `Merge` 노드에서 재결합된다. `Build MD Content`가 YAML frontmatter와 Obsidian 링크 문법을 포함한 Markdown 본문을 만들고, `uproad to drive`가 OneDrive의 `옵시디언/Startegy_Investment/Telegram/{date}/` 경로에 `.md` 파일을 업로드한다. 마지막으로 `Send Success`가 저장 완료 메시지를 텔레그램으로 보낸다.

### 뉴스 브리핑 자동화

`Schedule Trigger`는 매일 `07:30`에 실행되고, `Manual Trigger`는 수동 점검용으로 사용된다. 워크플로우는 연합뉴스 경제/세계 RSS, CNBC RSS, Yahoo Finance RSS를 읽고 `Set * Source` 노드에서 출처를 부여한 뒤 `Merge News Sources`로 합친다.

`Indexing`과 `Normalize Article Fields`는 제목, 본문, 날짜, URL, 출처를 공통 스키마로 맞춘다. `Filter By Time`은 최근 기사만 남기고, `속보, 특징주, 영상, 쇼츠 필터링`은 브리핑 대상에서 제외할 항목을 거른다. `Read Archive URLs`와 `Aggregate Archive URLs`는 Google Sheets의 뉴스 아카이브를 읽어 기존 URL 목록을 만들고, `Merge Before Dedup`과 `Filter New Articles`가 신규 기사만 통과시킨다.

각 기사는 `Loop Over Items`에서 순회되며 `AI Country Classifier`, `AI subject Classifier`, `AI Scoring`으로 국가, 주제, 중요도를 부여받는다. `Switch By Country`와 국가별 `Switch By Subject_*`, `Top N *` 노드는 미국/중국/한국/기타별 주요 기사를 선별한다. 이후 `Switch By Source`가 출처별 HTML 수집 경로로 나누고, `HTTP Request *`와 `HTML *`가 원문 본문을 추출한다. 출처별 `Merge` 노드는 원본 기사 메타데이터와 HTML 추출 결과를 다시 연결한다.

`AI Summarizer`는 `OpenAI Summary Model`의 `gpt-4o`로 제목과 요약을 한국어 JSON으로 생성한다. `Parse Summary`가 결과를 구조화하고, `시장 데이터 조회 + 메시지 포맷`은 주중에 시장 데이터를 추가한다. `Merge market data`와 `Assemble Message`가 MarkdownV2 텔레그램 메시지를 조립하며, `Send Telegram`이 `@undergroundresearch36` 채널로 발행한다. 별도의 연합뉴스 속보 RSS 트리거는 `[속보]`, `[특징주]` 탐지 후 `텔레그램 속보 알림`으로 즉시 알림을 보낸다.

### 경제지표 차트 자동화

`RSS Feed Trigger`와 `RSS S1N9 (유가)`는 연합인포맥스 RSS를 주기적으로 폴링한다. `Filter`는 `[서환-마감]`, `[채권-마감]`, `[뉴욕유가]` 제목만 통과시키고, `키워드별 분류`가 `exchange`, `oil`, `bond` 카테고리를 부여한다.

`HTTP Request Article`은 기사 URL을 가져오고 `Extract Article HTML`은 `#article-view-content-div`에서 본문을 추출한다. `Merge Article Data`는 RSS 메타데이터와 HTML 본문을 합친 뒤 `Parse Exchange`, `Parse Oil`, `Parse Bond`에 전달한다. 각 파서 노드는 날짜, 달러-원 환율, WTI, 국고채 3년/10년 금리, 기사 리드 문단을 정규표현식으로 추출한다.

`Build Comment Prompt`는 추출된 지표와 기사 내용을 AI 분석 프롬프트로 만들고, `AI Agent`가 `gpt-4o` 기반 코멘트를 생성한다. 지표 데이터와 코멘트는 `Merge`, `Merge1`, `Merge2`를 거쳐 각각 `Append Exchange Sheet`, `Append Oil Sheet`, `Append Bond Sheet`로 Google Sheets에 저장된다.

저장 후 `Switch`가 지표 카테고리별로 기존 Sheets 데이터를 읽는다. `환율 Data`, `유가 Data`, `국고채 Data`는 같은 Google Sheets 문서의 각 탭을 조회하고, `기간 필터`는 최근 60일 자료만 통과시킨다. `Build QuickChart JSON`은 환율, WTI, 국고채 라인 차트 JSON을 만들고 `Send to QuickChart`가 QuickChart.io에 차트 생성을 요청한다. `Send Chart Photos`는 차트 이미지를 텔레그램 채널에 보내며, `Merge Chart+Comment` 후 `Send Comment Text`가 AI 코멘트를 추가 발행한다.

## 외부 서비스 의존 관계

```text
Telegram 사용자/채널
  -> n8n Telegram Trigger / Telegram nodes
  -> Telegram Bot API

n8n on Railway
  -> OpenAI API
       - gpt-4o-mini: Telegram 노트 제목/태그 JSON 생성
       - gpt-4o: 뉴스 요약, 경제지표 코멘트
  -> Microsoft Graph API / OneDrive
       - Obsidian vault Markdown 및 첨부파일 저장
  -> Google Sheets API
       - 뉴스 아카이브 URL 저장/조회
       - 환율, 유가, 국고채 시계열 저장/조회
  -> RSS feeds
       - 연합뉴스/연합인포맥스 RSS
       - CNBC RSS
       - Yahoo Finance RSS
  -> QuickChart.io
       - 경제지표 라인 차트 이미지 생성
  -> HTTP article pages
       - 기사 본문 HTML 추출
```

## 공통 패턴

### RSS 파싱 패턴

RSS 입력은 먼저 출처 또는 카테고리를 명시적으로 부여한다. 뉴스 브리핑은 `Set Yonhap Source`, `Set CNBC Source`, `Set Yahoo Source`로 출처를 고정한 뒤 공통 필드로 정규화한다. 경제지표 자동화는 제목 키워드로 `exchange`, `oil`, `bond`를 분류한 뒤 기사 HTML을 추가 조회해 실제 수치를 추출한다.

중복 처리는 Google Sheets 아카이브와 현재 실행 내 `seenUrls` 집합을 함께 사용한다. RSS GUID나 URL이 변할 수 있으므로, 운영 중 중복이 보이면 URL 정규화 또는 제목+날짜 기반 보조 키를 추가하는 것이 우선 개선 지점이다.

### AI 코멘트 생성 패턴

복잡한 판단이 필요한 단계는 n8n LangChain `AI Agent` 노드를 사용한다. 뉴스 브리핑의 국가/주제/점수 분류와 최종 요약, 경제지표 자동화의 시장 코멘트가 여기에 해당한다. 반대로 Telegram to Obsidian의 제목/태그 생성처럼 짧은 JSON 응답만 필요한 경우에는 HTTP Request로 OpenAI REST API를 직접 호출하고 `strict: true` JSON Schema를 적용한다.

AI 출력은 바로 최종 메시지에 쓰지 않고 `Parse Summary` 같은 코드 노드에서 JSON 파싱과 fallback 정규식을 거친다. 이 패턴은 모델 응답이 코드블록 또는 느슨한 JSON으로 흔들릴 때 텔레그램 발행 실패를 줄인다.

### 텔레그램 전송 패턴

텔레그램 출력은 목적에 따라 세 가지로 나뉜다.

- 개인 봇 응답: Telegram to Obsidian의 `Send Success`는 저장 성공 여부를 사용자에게 알려준다.
- 채널 브리핑: 뉴스 브리핑의 `Send Telegram`은 MarkdownV2 이스케이프가 적용된 긴 메시지를 `@undergroundresearch36`로 보낸다.
- 차트/코멘트 발행: 경제지표 자동화는 `Send Chart Photos`로 QuickChart 이미지를 먼저 보내고 `Send Comment Text`로 해설 텍스트를 이어서 보낸다.

MarkdownV2를 사용하는 메시지는 `Assemble Message`에서 특수문자를 이스케이프한다. 링크 미리보기와 attribution 옵션은 메시지 성격에 맞춰 노드별로 명시한다.

## 인프라 구성

```text
Railway
  └─ n8n production instance
       ├─ workflow: Telegram to Obsidian
       ├─ workflow: 뉴스 브리핑 자동화
       └─ workflow: 경제지표 차트 자동화

OneDrive
  └─ 옵시디언/Startegy_Investment/
       └─ Telegram/
            ├─ {date}/YYYY-MM-DD_title.md
            └─ attachments/

Google Sheets
  ├─ 뉴스 아카이브
  │    └─ 발행/처리된 기사 URL 중복 방지
  └─ 경제지표 차트 자동화
       ├─ 환율
       ├─ 유가
       └─ 국고채

Telegram
  ├─ 저장 요청 입력 봇
  └─ @undergroundresearch36 채널 발행
```

워크플로우의 `settings`는 `executionOrder: v1`, `callerPolicy: workflowsFromSameOwner`, `availableInMCP: false`를 공통적으로 사용한다. 뉴스 브리핑과 경제지표 차트 자동화는 `timezone: Asia/Seoul`, `binaryMode: separate`도 설정되어 있다.
