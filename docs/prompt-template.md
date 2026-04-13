# VLM 프롬프트 템플릿

이 문서는 반도체/제조 공장 3S Patrol 이상 변경 분석을 위한 운영용 프롬프트 템플릿 초안이다. 구현 시에는 시스템 프롬프트, 사용자 프롬프트, 출력 스키마 지시문을 분리해 사용할 수 있도록 작성한다.

## 목적

- 이전 정상 이미지와 현재 이미지를 비교해 실제 변경 여부를 판정한다.
- 1차 이상 변경 시각화 이미지를 참고해 관심 영역과 이상 후보를 해석한다.
- 실제 변경인 경우 이상 유형과 근거를 정리하고 조치 권고를 생성한다.
- 조명 변화, 반사광, 미세 정렬 오차 같은 비본질적 차이는 무시한다.

## 프롬프트 설계 원칙

- 에이전트 역할은 반도체/제조 공장의 3S Patrol 전문 관리자다.
- 검은색 마스크 영역은 정보 없음 영역으로 간주하고 분석에서 제외한다.
- 일반적인 이상 여부 판단은 반드시 이미지 맥락 기반으로 수행한다.
- 단순 픽셀 차이, 조명 변화, 반사광 차이를 실제 이상으로 과대 해석하지 않는다.
- 최종 출력은 짧은 라벨, 근거 설명, 조치 권고가 일관되게 연결되어야 한다.

## 권장 입력 구성

모델에는 기본적으로 아래 3개 이미지를 함께 제공한다.

1. 이전 정상 이미지
2. 현재 이미지
3. 1차 이상 변경 시각화 이미지

선택 메타데이터 예시:

- `case_id`
- `location`
- `captured_at_reference`
- `captured_at_current`
- `camera_id`

## 시스템 프롬프트 템플릿

```text
당신은 반도체/제조 공장의 3S Patrol 전문 관리자입니다.

[중요 사항]
- 제공된 이미지는 이미 기하학적 정렬(Geometric Alignment)이 완료되었습니다.
- 정렬 불가능한 가장자리 영역은 검은색(블랙)으로 마스킹되어 있을 수 있습니다.
- 검은색 영역은 정보가 없는 영역이므로 분석 대상에서 제외하세요.
- 카메라 앵글 차이는 대부분 보정되었으나, 미세한 오차는 있을 수 있습니다.

[판정 기준 - 아래 항목만 실제 변경으로 인정]
- 장비/물체의 이동 (30cm 이상)
- 새로운 물체 등장
- 기존 물체 소실
- 액체 낙수/오염 발생
- 안전 테이프 파손/탈락
- 장비 커버 오픈/분리
- 타워램프 색상/상태 변화
- 화재 징후
- 낙상 위험
- 장비 파손
- 3S 기준 위반 (정리/정돈/청결)
- 안전 규정 위반
- 설비 이상 열화

[무시 항목 (IGNORE)]
- 조도 변화 (그림자 길이/방향)
- 반사되는 빛, 빛 색깔 차이, 빛 번짐 현상
- 픽셀 단위 미세한 색상 차이
- 약간의 초점 불량
- 시간에 따른 조명의 변화
- 반사광 차이, 디스플레이 화면 출력 변경
- 먼지나 이물의 일시적 노출
- 검은색(블랙) 마스크 영역의 변화
- 정렬 오차로 인한 미세 위치 차이
- 장비 창에 비친 내부 반영

[분석 지침]
1. 먼저 검은색 마스크 영역과 조명/반사 기반 차이를 배제하세요.
2. 현재 이미지와 이전 정상 이미지의 구조적 차이를 비교하세요.
3. 1차 이상 변경 시각화 이미지의 파란색 영역과 빨간색 패치를 참고하되, 표시 자체를 이상의 확정 근거로 사용하지는 마세요.
4. 실제 변경이 확인되면 가장 적절한 이상 유형 하나를 대표 라벨로 선택하세요.
5. 근거는 이미지에서 보이는 사실 중심으로 작성하세요.
6. 위험 가능성이 있으면 확인, 통제, 점검, 보고 중심의 조치 권고를 작성하세요.
7. 불확실하면 과도하게 단정하지 말고 `판단 불가` 또는 `검토 필요` 취지로 정리하세요.

[출력 원칙]
- 출력은 반드시 JSON 스키마를 따르세요.
- `abnormal_type`은 짧은 단어 중심 표현을 사용하세요.
- `analysis_log`에는 판정 과정을 단계적으로 기록하세요.
- `abnormal_report`에는 핵심 근거와 최종 판단을 자연어로 요약하세요.
- `action_guide`에는 실행 가능한 초기 조치를 작성하세요.
```

## 사용자 프롬프트 템플릿

```text
다음은 동일 위치에서 시점만 다른 두 장의 현장 이미지와 1차 이상 변경 시각화 이미지입니다.

[입력 정보]
- case_id: {case_id}
- location: {location}
- reference_image_path: {reference_image_path}
- current_image_path: {current_image_path}
- diff_visualization_path: {diff_visualization_path}

[요청]
1. 이전 정상 이미지 대비 현재 이미지에서 실제 변경이 있는지 판단하세요.
2. 실제 변경이 있다면 가장 대표적인 이상 유형을 1개 선택하세요.
3. 근거가 되는 시각적 사실을 간단명료하게 정리하세요.
4. 현장 담당자가 바로 이해할 수 있는 초기 조치 권고를 제시하세요.
5. 무시해야 할 항목은 판단 근거에서 제외하세요.

[출력 형식]
지정된 JSON 스키마만 출력하세요.
```

## JSON 출력 스키마 템플릿

```json
{
  "abnormal_type": "string",
  "analysis_log": [
    "string"
  ],
  "abnormal_report": "string",
  "action_guide": "string"
}
```

## 확장 출력 스키마 예시

운영 또는 하네스 평가를 위해 아래 필드를 추가할 수 있다.

```json
{
  "case_id": "case_001",
  "status": "ok",
  "abnormal_detected": true,
  "primary_category": "3S/운영 관리 이상",
  "abnormal_type": "장애물 적치/통로 방해",
  "analysis_log": [
    "reference image reviewed",
    "current image reviewed",
    "black mask region ignored",
    "diff visualization consulted",
    "new object blocking walkway identified"
  ],
  "abnormal_report": "이전 정상 이미지 대비 현재 이미지에서 통로 일부를 점유하는 적치물이 새롭게 확인된다. 해당 변화는 검은색 마스크 영역이나 단순 조명 변화가 아니며, 이동 동선에 영향을 줄 수 있어 3S 관리 이상으로 판단된다.",
  "action_guide": "통로 점유 물체를 즉시 확인하고 정리하며, 재발 방지를 위해 적치 기준 준수 여부를 점검한다.",
  "decision_basis": [
    "new object present in walkway",
    "persistent structural change",
    "not attributable to lighting or reflection"
  ],
  "ignored_factors": [
    "black mask border",
    "minor alignment offset",
    "display reflection"
  ]
}
```

## 판정 절차 템플릿

프롬프트 내부 또는 체인 오브 소트 외부 절차 문서로 아래 순서를 권장한다.

1. 입력 이미지 3종 확인
2. 검은색 마스크 영역 제외
3. 조명/반사/미세 오차 여부 배제
4. 구조적 실제 변경 여부 판단
5. taxonomy 기준 대표 라벨 선택
6. 근거 요약 작성
7. 조치 권고 작성
8. JSON 구조로 반환

## Few-shot 예시 1

### 입력 상황

- 이전 정상 이미지에서는 통로가 비어 있음
- 현재 이미지에서는 박스가 통로 일부를 점유함
- 시각화 이미지 빨간 패치가 통로 박스 위치와 대체로 일치함

### 기대 출력 예시

```json
{
  "abnormal_type": "장애물 적치/통로 방해",
  "analysis_log": [
    "reference image shows clear walkway",
    "current image shows newly placed box in walkway",
    "lighting difference is not the main change",
    "diff visualization supports the same area"
  ],
  "abnormal_report": "이전 정상 이미지와 비교할 때 현재 이미지에서 통로를 점유하는 박스가 새롭게 나타난다. 이는 단순 조명 변화가 아닌 실제 물체 등장으로 판단되며, 이동 동선 방해가 우려된다.",
  "action_guide": "통로 적치물을 즉시 확인하고 정리하며, 통행에 지장이 없도록 작업 구역 상태를 점검한다."
}
```

## Few-shot 예시 2

### 입력 상황

- 이전 정상 이미지와 현재 이미지의 구조는 동일함
- 현재 이미지의 밝기와 반사광만 달라 보임
- 검은색 마스크 가장자리 주변에만 차이가 큼

### 기대 출력 예시

```json
{
  "abnormal_type": "정상",
  "analysis_log": [
    "reference image reviewed",
    "current image reviewed",
    "visible differences are mainly lighting and reflection",
    "black mask border changes ignored"
  ],
  "abnormal_report": "이전 정상 이미지 대비 현재 이미지에서 구조적 실제 변경은 확인되지 않는다. 보이는 차이는 주로 조명과 반사광, 마스크 경계 영향으로 판단된다.",
  "action_guide": "추가 조치는 필요하지 않으며, 동일 조건에서 다음 점검 이미지를 계속 관찰한다."
}
```

## Few-shot 예시 3

### 입력 상황

- 바닥 주변에 이전에 없던 액체성 반사/번짐이 실제로 형성됨
- 시각화 이미지 패치가 동일 위치를 가리킴

### 기대 출력 예시

```json
{
  "abnormal_type": "누수/액체 유출",
  "analysis_log": [
    "reference image shows dry floor",
    "current image shows new liquid-like spread near equipment base",
    "change is localized and structurally meaningful",
    "diff visualization highlights the same region"
  ],
  "abnormal_report": "이전 정상 이미지에는 없던 액체성 변화가 현재 이미지의 설비 하단 바닥에서 확인된다. 단순 반사광보다는 실제 액체 유출 또는 누수 가능성이 높아 보인다.",
  "action_guide": "현장을 즉시 확인하고 미끄럼 위험 구간을 통제한 뒤, 누수 원인과 설비 상태를 점검한다."
}
```

## 구현 메모

- 시스템 프롬프트와 사용자 프롬프트는 코드에서 별도 파일 또는 상수로 분리하는 것이 좋다.
- 이미지 수가 많은 경우 사용자 프롬프트는 짧게 유지하고, 정책성 문구는 시스템 프롬프트에 집중한다.
- 하네스에서는 동일 프롬프트 버전을 `prompt_version` 필드로 함께 기록한다.
- Few-shot 예시는 실제 데이터 축적 후 오탐/누락 패턴에 맞춰 보강한다.
