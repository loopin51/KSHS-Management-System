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
*
  ======
# KSHS-Management-System
강원과학고의 시약, 장비, 물품등의 대여 및 관리를 위한 프로젝트

이 프로젝트는 Python의 Gradio 프레임워크와 Supabase를 백엔드로 활용하여 장비 대여 및 관리를 위한 웹 애플리케이션을 구축하는 것을 목표로 합니다. 사용자 역할(일반 사용자/관리자)에 따라 다른 인터페이스와 접근 권한을 제공하여 효율적인 장비 관리를 지원합니다.

---

## 1. 프로젝트 개요

이 앱은 크게 두 가지 주요 사용자 그룹을 위한 기능을 제공합니다:

* **일반 사용자 (로그인 불필요):**
    * **부서별 장비 조회:** `물리과`, `화학과`, `IT과` 중 부서를 선택하면 해당 부서의 모든 장비 목록과 장비별 대여 가능 여부가 표시됩니다.
    * **장비 검색:** 검색창에 장비의 ID 또는 이름을 입력하여 조건에 맞는 장비를 필터링하여 조회할 수 있습니다.
    * **장비 대여 신청:**
        * 검색 탭에서 필요한 장비들을 **체크박스로 선택**합니다.
        * "대여" 버튼을 누르면 "대여" 탭으로 자동 이동하고, 선택된 장비 목록이 표시됩니다.
        * 대여 기간, 대여자 이름, 사용 목적을 입력합니다.
        * "확인" 버튼 클릭 시, **선택된 장비와 대여 기간이 기존 대여 기록과 겹치는지 백엔드에서 확인**합니다.
        * 충돌이 있는 경우 **에러 메시지**를 표시하고, 충돌이 없는 경우 대여 신청이 완료되었음을 알리는 메시지와 함께 백엔드에서 대여 요청을 처리합니다.

* **관리자 (로그인 필요):**
    * 시스템 내 모든 장비 현황 조회
    * 새로운 장비 추가 (장비 ID 등록 시 규칙 적용)
    * 기존 장비 정보 수정

UI/UX 개선을 위해 기능을 탭으로 나누어 직관적인 사용 경험을 제공합니다.

---

## 2. 주요 기술 스택

* **프론트엔드 (UI):** **Gradio**
    * 빠르게 웹 기반 인터페이스를 구축할 수 있는 Python 라이브러리입니다.
    * `gr.Tabs()`, `gr.TabItem()`, `gr.Column()`, `gr.Row()`, `gr.State()` 등 다양한 컴포넌트를 사용하여 동적인 UI를 구현합니다.
    * `visible` 속성을 통해 사용자 역할에 따라 UI 컴포넌트의 가시성을 제어합니다.
    * **`gr.CheckboxGroup`** 또는 `gr.Dataframe`의 선택 기능을 활용하여 장비 선택을 구현합니다.

* **백엔드 (인증 & 데이터베이스):** **Supabase**
    * PostgreSQL 기반의 오픈 소스 Firebase 대체재입니다.
    * **인증 (Auth):** 이메일/비밀번호 로그인, 소셜 로그인 등 강력한 인증 기능을 제공합니다. 직접 인증 시스템을 구축할 필요 없이 Supabase의 API를 활용합니다.
    * **데이터베이스:** 안정적인 PostgreSQL 데이터베이스를 제공하며, `Row Level Security (RLS)`를 통해 데이터 접근 권한을 세밀하게 제어할 수 있습니다. **장비 대여 기록(`rentals` 테이블 등)을 저장하고, 대여 충돌 확인 로직을 백엔드에서 처리**합니다.
    * **Python 클라이언트:** `supabase-py` 라이브러리를 사용하여 Python에서 Supabase 서비스와 쉽게 상호작용합니다.

* **데이터베이스 ORM (선택 사항):** **SQLAlchemy**
    * Python에서 데이터베이스를 객체 지향적으로 다룰 수 있게 해주는 ORM (Object-Relational Mapper)입니다.
    * Supabase의 PostgreSQL 데이터베이스와 연동하여 사용할 수 있습니다. (하지만 Supabase의 RLS를 최대한 활용하려면 `supabase-py`를 통한 직접적인 데이터 상호작용이 더 효율적일 수 있습니다.)

* **패키지 매니저:** **uv**
    * 빠르고 효율적인 Python 패키지 설치 및 환경 관리를 위해 `uv`를 사용합니다.

---

## 3. 핵심 기능 구현 방법 (간단한 원리)

### 3.1. 사용자 인증 및 역할 관리

1.  **Supabase 프로젝트 설정:**
    * Supabase 웹사이트에서 프로젝트를 생성하고, `Authentication` 섹션에서 이메일/비밀번호 로그인을 활성화합니다.
    * `Database` 섹션에서 `users` 테이블 (Supabase Auth에서 자동 생성) 외에 `equipments` (장비 정보), 그리고 **`rentals` (대여 기록)** 테이블을 PostgreSQL 문법으로 생성합니다.
        * `equipments` 테이블: `department`, `id` (관리자 등록 규칙 적용), `name`, `quantity`, `available_quantity` 등의 필드
        * `rentals` 테이블: `equipment_id` (장비 외래 키), `start_date`, `end_date`, `borrower_name`, `purpose` 등의 필드
    * **Row Level Security (RLS) 정책 설정:** 가장 중요합니다. 예를 들어, `equipments` 테이블에 일반 사용자는 조회만 가능하고, 관리자는 모든 CRUD(생성, 읽기, 업데이트, 삭제) 작업을 수행할 수 있도록 RLS 정책을 정의합니다. `rentals` 테이블에 대해서도 대여 신청, 조회 등에 대한 RLS를 설정합니다.

2.  **Python 백엔드 연동 (`supabase-py`):**
    * `supabase-py` 라이브러리를 사용하여 사용자 등록, 로그인, 로그아웃 기능을 구현합니다.
    * 로그인 성공 시, Supabase에서 반환하는 사용자 정보(특히 `role` 필드)를 Gradio 앱의 `gr.State()` 컴포넌트에 저장합니다.

### 3.2. Gradio UI 구성 및 역할 기반 접근 제어

1.  **메인 탭 레이아웃:**
    * `gr.Blocks()` 내부에 `gr.Tabs()`를 사용하여 전체 앱의 기본 탭 구조를 만듭니다.
    * **"장비 조회 및 검색" 탭:** `gr.TabItem("🔎 장비 조회 및 검색", visible=True)`로 설정하여 로그인 여부와 관계없이 항상 보이도록 합니다.
        * 이 탭 내부에 **부서 선택 드롭다운**, **검색창**(`gr.Textbox`), 그리고 검색 결과와 장비별 대여 가능 여부를 표시할 `gr.Dataframe`을 배치합니다.
        * `gr.Dataframe`의 선택 가능한 행 기능을 활용하여 장비 선택을 구현합니다.
        * 선택된 장비를 "대여" 탭으로 전달하기 위한 **"대여" 버튼**을 추가합니다.
    * **"장비 대여" 탭:** `gr.TabItem("📝 장비 대여", visible=True)`로 설정하여 항상 보이도록 합니다.
        * 이 탭은 **`gr.State()`**를 사용하여 "장비 조회 및 검색" 탭에서 선택된 장비 목록을 받아서 표시합니다.
        * 대여 기간(`gr.Date` 또는 `gr.Textbox`로 시작/종료일), 대여자 이름(`gr.Textbox`), 사용 목적(`gr.Textbox`)을 입력받는 폼을 배치합니다.
        * "확인" 버튼(`gr.Button`) 클릭 시 백엔드 대여 요청 함수를 호출합니다.
    * **"관리자 로그인" 탭:** `gr.TabItem("🔑 관리자 로그인", visible=True)`로 설정하여 초기 화면에 보이지만, 관리자 로그인 성공 시 `gr.update(visible=False)`로 숨겨집니다.
    * **"장비 관리" 탭:** `gr.TabItem("⚙️ 장비 관리", visible=False)`로 설정하여 초기에는 숨겨져 있다가, 관리자 로그인 성공 시 `gr.update(visible=True)`로 보이도록 합니다. 이 탭 내부에 "모든 장비 현황"과 "장비 추가/수정" 같은 하위 탭을 구성할 수 있습니다.

2.  **동적 UI 변경:**
    * `login_user()` 및 `logout_user()` Gradio 함수 내에서 `gr.update(visible=...)`를 사용하여 특정 탭이나 컴포넌트의 가시성을 제어합니다.
    * 로그인 성공 시 `gr.Tabs(selected=...)`를 사용하여 관리자용 탭으로 자동으로 전환시킵니다.
    * `gr.State()` 컴포넌트에 현재 로그인된 사용자 정보(`user_id`, `role` 등)를 저장하고, 이 정보를 기반으로 특정 기능(`get_admin_equipment_data`, `add_edit_equipment` 등)의 실행 여부를 제어합니다.
    * **"대여" 버튼 클릭 시 `main_tabs`의 `selected` 속성을 "장비 대여" 탭으로 변경하고, `gr.State()`를 통해 선택된 장비 정보를 전달**합니다.

3.  **데이터 조회/조작:**
    * **일반 사용자 조회/검색:**
        * 부서 선택 드롭다운(`gr.Dropdown`)의 `change` 이벤트 또는 별도의 "조회" 버튼 클릭 시, 선택된 부서에 해당하는 장비 데이터를 Supabase에서 가져옵니다.
        * `supabase-py`의 `select()` 쿼리를 사용하여 RLS에 따라 접근 가능한 장비 데이터만 가져와 `gr.Dataframe`으로 표시합니다.
        * **검색 기능:** 검색창(`gr.Textbox`)에 입력된 ID 또는 이름을 기반으로 Supabase 쿼리(`filter` 또는 `ilike`)를 사용하여 장비 목록을 필터링하고 `gr.Dataframe`을 리로드합니다.
    * **장비 대여 요청 처리:**
        * "확인" 버튼 클릭 시, 선택된 장비 정보, 대여 기간, 대여자 정보 등을 백엔드 함수로 전달합니다.
        * 백엔드에서는 `rentals` 테이블을 조회하여 **선택된 장비의 ID와 요청된 대여 기간이 기존 대여 기록과 겹치는지 확인하는 로직**을 수행합니다.
        * 충돌 시, `gr.Error()` 또는 메시지(`gr.Textbox`)를 통해 사용자에게 에러 메시지를 표시합니다.
        * 충돌이 없는 경우, `rentals` 테이블에 새로운 대여 기록을 삽입하고, 성공 메시지를 표시합니다. 동시에 `equipments` 테이블의 `available_quantity`를 업데이트할 수 있습니다.
    * **관리자 조회/조작:** 관리자 로그인 후, `gr.Dataframe`으로 모든 장비 데이터를 조회하고, 입력 필드(`gr.Textbox`, `gr.Dropdown`)와 버튼을 사용하여 장비 정보를 추가, 수정합니다. 이 모든 작업은 Supabase의 보호된 API를 통해 이루어져야 합니다.

### 3.3. 초기 UI 로드 및 상태 유지

* `demo.load()` 이벤트 핸들러를 사용하여 앱이 처음 로드될 때 `initial_load_ui_state()` 함수를 실행합니다.
* 이 함수는 Supabase에서 현재 세션(또는 토큰)을 확인하여 사용자가 이미 로그인되어 있는지 파악하고, 그에 따라 초기 탭 선택과 각 탭의 가시성(`visible` 속성)을 설정합니다.

---

## 4. 개발 환경 설정

1.  **Python 설치:**
    * Python 3.8 이상 버전을 설치합니다.

2.  **`uv` 패키지 매니저 설치:**
    ```bash
    pip install uv
    ```

3.  **가상 환경 생성 및 활성화:**
    ```bash
    uv venv
    source .venv/bin/activate  # macOS/Linux
    .venv\Scripts\activate     # Windows
    ```

4.  **필요한 라이브러리 설치:**
    ```bash
    uv pip install gradio supabase-py psycopg2-binary python-dotenv
    # SQLAlchemy를 직접 사용하려면:
    # uv pip install sqlalchemy
    ```

5.  **Supabase 프로젝트 설정:**
    * Supabase 웹사이트에서 새 프로젝트를 생성합니다.
    * 프로젝트 대시보드에서 **`Project URL`**과 **`Anon Public Key`**를 확인합니다. 이 정보는 환경 변수로 설정하여 사용합니다.
    * 데이터베이스에 `equipments` 테이블을 생성하고, `department` (물리과, 화학과, IT과), `id` (관리자 등록 규칙 적용), `name`, `quantity`, `available_quantity` 등의 필드를 정의합니다.
    * **`rentals` 테이블을 생성하고, `equipment_id` (장비 외래 키), `start_date`, `end_date`, `borrower_name`, `purpose` 등의 필드를 정의합니다.**
    * RLS 정책을 설정하여 일반 사용자는 조회 및 대여 신청만 가능하고, 관리자는 모든 작업을 수행할 수 있도록 합니다.

6.  **환경 변수 설정:**
    * 프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가합니다 (보안을 위해 실제 값은 대체하세요):
        ```
        SUPABASE_URL="YOUR_SUPABASE_PROJECT_URL"
        SUPABASE_KEY="YOUR_SUPABASE_ANON_PUBLIC_KEY"
        ```
    * 코드 상단에 `from dotenv import load_dotenv; load_dotenv()`를 추가하여 `.env` 파일의 환경 변수를 로드합니다.

---

## 5. 프로젝트 실행 방법

1.  위에서 설명한 개발 환경 설정을 완료합니다.
2.  Gradio 앱 코드 (이전 대화에서 제공된 예시 코드에 위에서 논의된 대여 신청 및 관련 기능 추가)를 `app.py`와 같은 파일로 저장합니다.
3.  터미널에서 가상 환경이 활성화된 상태에서 다음 명령어를 실행합니다:
    ```bash
    python app.py
    ```
4.  Gradio가 실행되면 제공되는 로컬 URL (`http://127.0.0.1:7860` 또는 유사한 주소)로 웹 브라우저를 통해 접속합니다.

---
>>>>>>> main
