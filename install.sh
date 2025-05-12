#!/bin/bash
set -e

# 현재 스크립트 경로로 이동
cd "$(dirname "$0")"

echo "========================================================================="
echo
echo "  Python venv Launcher"
echo "  This version does NOT use conda"
echo
echo "========================================================================="
echo

# conda 환경 비활성화는 필요 없음 (bash에서는 그냥 무시)

# 가상환경 디렉토리 지정
VENV_DIR="./venv"

# Python 설치 여부 확인
if ! command -v python3 &> /dev/null; then
    echo "Python does not exist."
    exit 1
fi

# 가상환경이 없는 경우 생성
if [ ! -f "$VENV_DIR/bin/python" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR" || {
        echo "Could not create virtual environment."
        exit 1
    }
    echo "Virtual environment created at $VENV_DIR"
fi

# 가상환경 활성화
source "$VENV_DIR/bin/activate"

# 필요한 패키지 설치
echo "Installing required packages..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt || {
    echo "Could not install required packages."
    exit 1
}

# (여기에 스크립트 실행 코드 추가 가능)

# 끝
read -p "Press enter to exit."