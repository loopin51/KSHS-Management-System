# 장비 대여 및 관리 앱 (Equipment Rental and Management App)

Python Gradio 프레임워크와 Supabase 백엔드를 활용하여 구축된 장비 대여 및 관리 웹 애플리케이션입니다. 사용자 역할(일반 사용자/관리자)에 따라 다른 인터페이스와 접근 권한을 제공하여 효율적인 장비 관리를 지원합니다.

## 주요 기능

*   **일반 사용자**:
    *   부서별 장비 조회 및 검색 (ID 또는 이름)
    *   장비 대여 가능 여부 확인
    *   장비 대여 신청 (대여 기간, 대여자 이름, 사용 목적 입력) - 로그인 필요
*   **관리자**:
    *   시스템 내 모든 장비 현황 조회
    *   새로운 장비 추가 (ID, 이름, 부서, 수량)
    *   기존 장비 정보 수정
    *   (로그인 시 관리자 이메일 환경변수 기반으로 역할 구분)

## 기술 스택

*   **프론트엔드 (UI)**: Gradio
*   **백엔드 (인증 & 데이터베이스)**: Supabase (PostgreSQL)
*   **Python 라이브러리**: supabase-py, python-dotenv, pandas
*   **패키지 매니저 (권장)**: uv 또는 pip

## 1. Supabase 백엔드 설정

**중요**: 이 애플리케이션을 실행하기 전에 Supabase 프로젝트를 설정하고 필요한 테이블과 정책을 구성해야 합니다. 자세한 단계는 [여기](#detailed-supabase-setup-steps-to-be-provided-separately)를 참고하거나 이전에 제공된 설명을 따라주세요. (Jules가 별도로 제공한 Supabase 설정 단계를 참조하세요.)

간단 요약:
1.  Supabase 프로젝트 생성
2.  이메일/비밀번호 인증 활성화
3.  `equipments` 테이블 생성 (id, name, department, quantity, available_quantity) - RLS 활성화
4.  `rentals` 테이블 생성 (id, equipment_id, start_date, end_date, borrower_name, purpose, user_id) - RLS 활성화
5.  RLS 정책 설정:
    *   `equipments`: 일반 사용자 읽기 가능, 관리자 모든 작업 가능
    *   `rentals`: 사용자는 자신의 대여 기록 생성/읽기 가능, 관리자 모든 작업 가능
6.  Supabase 프로젝트 URL 및 Anon Public Key 확보

## 2. 로컬 개발 환경 설정

1.  **Python 설치**: Python 3.8 이상 버전을 권장합니다.
2.  **프로젝트 클론 또는 다운로드**:
    ```bash
    # git clone <repository_url> # 만약 Git 저장소에 있다면
    # cd <project_directory>
    ```
3.  **가상 환경 생성 및 활성화**:
    *   `uv` 사용 시:
        ```bash
        uv venv
        source .venv/bin/activate  # macOS/Linux
        # .venv\Scriptsctivate    # Windows
        ```
    *   `venv` (Python 기본) 사용 시:
        ```bash
        python -m venv .venv
        source .venv/bin/activate  # macOS/Linux
        # .venv\Scriptsctivate    # Windows
        ```
4.  **필요한 라이브러리 설치**:
    프로젝트 루트에 있는 `requirements.txt` 파일을 사용합니다.
    *   `uv` 사용 시:
        ```bash
        uv pip install -r requirements.txt
        ```
    *   `pip` 사용 시:
        ```bash
        pip install -r requirements.txt
        ```
    `requirements.txt` 내용:
    ```
    gradio
    supabase-py
    python-dotenv
    pandas
    psycopg2-binary
    ```

5.  **환경 변수 설정**:
    *   프로젝트 루트에 `.env.example` 파일이 있다면, 이를 `.env` 파일로 복사합니다. 없다면 새로 생성합니다.
    *   `.env` 파일을 열고 Supabase 프로젝트 정보와 관리자 이메일 주소를 입력합니다:
        ```env
        SUPABASE_URL="YOUR_SUPABASE_PROJECT_URL"
        SUPABASE_KEY="YOUR_SUPABASE_ANON_PUBLIC_KEY"
        ADMIN_EMAIL="your_admin_email@example.com"
        ```
        *   `YOUR_SUPABASE_PROJECT_URL`: Supabase 대시보드의 'Project Settings' > 'API' 섹션에 있는 Project URL 값입니다.
        *   `YOUR_SUPABASE_ANON_PUBLIC_KEY`: Supabase 대시보드의 'Project Settings' > 'API' 섹션에 있는 Project API keys의 `anon` `public` 키 값입니다.
        *   `your_admin_email@example.com`: 관리자로 인식될 사용자의 이메일 주소입니다. 이 이메일로 가입/로그인하면 관리자 기능을 사용할 수 있습니다.

## 3. 애플리케이션 실행

1.  위의 개발 환경 설정 단계를 모두 완료합니다.
2.  터미널에서 가상 환경이 활성화된 상태인지 확인합니다.
3.  프로젝트 루트 디렉토리에서 다음 명령어를 실행하여 Gradio 앱을 시작합니다:
    ```bash
    python app.py
    ```
4.  Gradio가 실행되면 터미널에 로컬 URL (일반적으로 `http://127.0.0.1:7860` 또는 유사한 주소)이 표시됩니다. 웹 브라우저를 열어 이 주소로 접속하면 애플리케이션을 사용할 수 있습니다.

## 애플리케이션 사용 방법

*   **초기 화면**: 장비 조회/검색, 장비 대여, 사용자 인증 탭이 표시됩니다.
*   **사용자 가입**: '사용자 인증' 탭에서 이메일과 비밀번호를 사용하여 새 계정을 등록할 수 있습니다. (Supabase 설정에 따라 이메일 확인이 필요할 수 있습니다.)
*   **로그인**: '사용자 인증' 탭에서 등록된 계정으로 로그인합니다.
    *   **일반 사용자 로그인 시**: '사용자 인증' 탭에 사용자 정보와 로그아웃 버튼이 표시되고, '장비 조회/검색' 탭으로 이동합니다. 장비 조회 및 대여 신청 기능을 사용할 수 있습니다.
    *   **관리자 로그인 시** (`.env` 파일에 설정된 `ADMIN_EMAIL`로 로그인): '사용자 인증' 탭이 숨겨지고, '장비 관리 (관리자)' 탭이 나타나며 해당 탭으로 자동 이동합니다. 관리자는 모든 장비 관리 기능을 사용할 수 있습니다.
*   **장비 조회**: '장비 조회 및 검색' 탭에서 부서별 또는 검색어를 통해 장비를 찾고, 대여 가능 수량을 확인할 수 있습니다.
*   **장비 대여 신청**: 조회된 장비 중 대여 가능한 항목을 선택 후 '대여 신청 페이지로' 버튼을 누르면 '장비 대여' 탭으로 이동합니다. 필요한 정보(날짜, 이름, 목적)를 입력하고 신청합니다. (로그인 필수)
*   **장비 관리 (관리자 전용)**:
    *   **모든 장비 현황 조회**: 등록된 모든 장비의 목록과 상세 정보(총량, 가용량 등)를 확인하고 새로고침할 수 있습니다. 목록에서 장비를 선택하면 '장비 추가/수정' 탭의 입력 필드가 자동으로 채워집니다.
    *   **장비 추가/수정**: 새 장비를 시스템에 추가하거나, 기존 장비의 정보를 수정합니다. ID, 이름, 부서, 총 수량을 관리합니다. (총 수량 변경 시 대여 중인 수량을 고려하여 가용 수량이 자동 계산됩니다.)
*   **로그아웃**: 각 역할별 화면(사용자 정보 또는 관리자 탭)에 있는 로그아웃 버튼을 사용하여 안전하게 로그아웃할 수 있습니다.

## 추가 정보

*   이 애플리케이션은 Supabase의 Row Level Security (RLS)를 활용하여 데이터 접근을 제어합니다.
*   관리자 기능은 `.env` 파일에 정의된 `ADMIN_EMAIL`을 통해 식별된 사용자에게만 제공됩니다.
```
