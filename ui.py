import sys
import json

import openpyxl
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QComboBox,
                               QLineEdit, QRadioButton, QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QMessageBox, QCheckBox)
from PySide6.QtCore import Qt
from openpyxl.utils import column_index_from_string
from openpyxl.utils.cell import coordinate_from_string

import src.solver.cpsat as cpsat
import src.solver.scip as scip
from src.problem.io import read_problem_from_excel, write_solution_to_excel, add_nothing_strategy

# 기본 설정값 (config.json이 없을 경우 사용)
DEFAULT_CONFIG = {
    "input": {
        "file_path": "data/200528_SK 계통(표준모델 적용).xlsm",
        "cost_range": "Z3:AC49",
        "cost_sheet": "04. reliability parameter for 3",
        "value_range": "A24:J71",
        "value_sheet": "05. results",
        "add_nothing_strategy": True
    },
    "solver": {
        "type": "SCIP",
        "problem_type": "cost_constraint",
        "cost_constraint": 1000,
        "value_weights": [1.0, 1.0, 1.0],
        "reliability_constraint": [150, 0.5, 0.5]
    },
    "output": {
        "file_path": "data/solution.xlsx",
        "sheet_name": "scip_cost_constraint"
    }
}

def load_config():
    """config.json 파일에서 설정을 로드합니다."""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"설정 파일 로드 오류: {e}, 기본 설정을 사용합니다.")
        return DEFAULT_CONFIG


def save_config(config):
    """현재 설정을 config.json 파일에 저장합니다."""
    try:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"설정 파일 저장 오류: {e}")
        return False


class OptimizationUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # config.json에서 설정 로드
        self.config = load_config()

        self.setWindowTitle("유지보수 전략 최적화")
        self.resize(900, 800)

        # 메인 위젯과 레이아웃 설정
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # UI 컴포넌트 생성
        self.create_settings_section()
        self.create_output_section()
        self.create_import_section()
        self.create_data_table()
        self.create_buttons()
        self.create_result_section()

        # 문제와 솔루션 저장 변수
        self.problem = None
        self.solution = None

        # 설정 값을 UI에 적용
        self.apply_config_to_ui()

        # 상태 업데이트
        self.update_constraint_visibility()

    def create_settings_section(self):
        # 문제 설정 섹션
        settings_label = QLabel("문제 설정")
        settings_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.main_layout.addWidget(settings_label)

        settings_layout = QGridLayout()

        # 첫 번째 행 - 솔버, 문제 유형 선택
        settings_layout.addWidget(QLabel("문제해결 solver"), 0, 0)
        settings_layout.addWidget(QLabel("풀이할 문제"), 0, 1)
        settings_layout.addWidget(QLabel("제약 조건"), 0, 2, 1, 3)

        self.solver_combo = QComboBox()
        self.solver_combo.addItems(["SCIP", "CP-SAT"])
        settings_layout.addWidget(self.solver_combo, 1, 0)

        self.problem_type_combo = QComboBox()
        self.problem_type_combo.addItems(["비용 제약", "민감도 제약"])
        self.problem_type_combo.currentIndexChanged.connect(self.update_constraint_visibility)
        settings_layout.addWidget(self.problem_type_combo, 1, 1)

        # 비용 제약 필드
        self.cost_constraint_label = QLabel("비용 제약")
        settings_layout.addWidget(self.cost_constraint_label, 1, 2)
        self.cost_constraint_input = QLineEdit()
        self.cost_constraint_input.setText("1000")
        self.cost_constraint_input.setFixedWidth(150)  # 너비 고정
        settings_layout.addWidget(self.cost_constraint_input, 1, 3, 1, 3)

        # 민감도 가중치 필드
        self.sensitivity_weights_label = QLabel("민감도 가중치")
        settings_layout.addWidget(self.sensitivity_weights_label, 2, 2)
        self.sensitivity_weights = []
        for i in range(3):
            weight_input = QLineEdit()
            weight_input.setText("1")
            weight_input.setFixedWidth(80)
            settings_layout.addWidget(weight_input, 2, 3 + i)
            self.sensitivity_weights.append(weight_input)

        # 민감도 제약 프레임 (이름 변경)
        self.sensitivity_constraint_frame = QFrame()
        sensitivity_layout = QGridLayout(self.sensitivity_constraint_frame)
        sensitivity_layout.addWidget(QLabel("민감도 제약"), 0, 0)

        self.sensitivity_labels = ["고장율", "ENS", "CIC"]
        self.sensitivity_constraints = []

        for i, label in enumerate(self.sensitivity_labels):
            sensitivity_layout.addWidget(QLabel(label), 0, i + 1)
            constraint_input = QLineEdit()
            constraint_input.setText("1")
            constraint_input.setFixedWidth(80)
            sensitivity_layout.addWidget(constraint_input, 1, i + 1)
            self.sensitivity_constraints.append(constraint_input)

        settings_layout.addWidget(self.sensitivity_constraint_frame, 3, 2, 2, 4)

        settings_layout.addWidget(QLabel("현상유지 전략:"), 4, 0)  # 행 번호는 기존 UI 구조에 맞게 조정
        self.add_nothing_checkbox = QCheckBox("문제 해결 시 '현상유지' 전략 추가")
        self.add_nothing_checkbox.setToolTip(
            "체크하면 '현상유지' 전략이 추가되고, 체크하지 않으면 아무 전략도 선택하지 않을 경우 비용과 가치가 0인 '현상유지'로 취급합니다.")
        settings_layout.addWidget(self.add_nothing_checkbox, 4, 1, 1, 5)

        self.main_layout.addLayout(settings_layout)

        self.main_layout.addLayout(settings_layout)

    def create_import_section(self):
        # 값 불러오기 섹션
        import_label = QLabel("값 미리보기")
        import_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.main_layout.addWidget(import_label)

        # 라디오 버튼
        radio_layout = QHBoxLayout()
        self.sensitivity_radio = QRadioButton("민감도 미리보기")
        self.sensitivity_radio.setChecked(True)
        self.cost_radio = QRadioButton("비용 미리보기")

        # 라디오 버튼 변경 이벤트 연결
        self.sensitivity_radio.toggled.connect(self.update_import_section)
        self.cost_radio.toggled.connect(self.update_import_section)

        radio_layout.addWidget(self.sensitivity_radio)
        radio_layout.addWidget(self.cost_radio)
        radio_layout.addStretch()
        self.main_layout.addLayout(radio_layout)

        # 민감도 입력 프레임
        self.sensitivity_frame = QFrame()
        sensitivity_layout = QHBoxLayout(self.sensitivity_frame)

        sensitivity_layout.addWidget(QLabel("파일명"))
        self.sensitivity_file_input = QLineEdit()
        self.sensitivity_file_input.setText(self.config["input"]["file_path"])
        sensitivity_layout.addWidget(self.sensitivity_file_input)

        sensitivity_layout.addWidget(QLabel("범위 셀"))
        self.sensitivity_range_input = QLineEdit()
        self.sensitivity_range_input.setText(self.config["input"]["value_range"])
        sensitivity_layout.addWidget(self.sensitivity_range_input)

        self.sensitivity_import_button = QPushButton("미리보기")
        self.sensitivity_import_button.clicked.connect(lambda: self.load_data("sensitivity"))
        sensitivity_layout.addWidget(self.sensitivity_import_button)

        self.main_layout.addWidget(self.sensitivity_frame)

        # 비용 입력 프레임
        self.cost_frame = QFrame()
        cost_layout = QHBoxLayout(self.cost_frame)

        cost_layout.addWidget(QLabel("파일명"))
        self.cost_file_input = QLineEdit()
        self.cost_file_input.setText(self.config["input"]["file_path"])
        cost_layout.addWidget(self.cost_file_input)

        cost_layout.addWidget(QLabel("범위 셀"))
        self.cost_range_input = QLineEdit()
        self.cost_range_input.setText(self.config["input"]["cost_range"])
        cost_layout.addWidget(self.cost_range_input)

        self.cost_import_button = QPushButton("불러오기")
        self.cost_import_button.clicked.connect(lambda: self.load_data("cost"))
        cost_layout.addWidget(self.cost_import_button)

        self.main_layout.addWidget(self.cost_frame)

        # 초기 상태 설정
        self.update_import_section()

    def create_output_section(self):
        # 출력 설정 섹션
        output_label = QLabel("출력 설정")
        output_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.main_layout.addWidget(output_label)

        output_layout = QGridLayout()

        # 출력 파일 경로
        output_layout.addWidget(QLabel("결과 파일 경로:"), 0, 0)
        self.output_file_input = QLineEdit()
        self.output_file_input.setText(self.config["output"]["file_path"])
        output_layout.addWidget(self.output_file_input, 0, 1, 1, 5)

        # 출력 시트 이름
        output_layout.addWidget(QLabel("결과 시트 이름:"), 1, 0)
        self.output_sheet_input = QLineEdit()
        self.output_sheet_input.setText(self.config["output"]["sheet_name"])
        output_layout.addWidget(self.output_sheet_input, 1, 1, 1, 5)

        self.main_layout.addLayout(output_layout)

    def create_data_table(self):
        # 데이터 테이블
        self.data_table = QTableWidget(8, 4)
        self.data_table.setHorizontalHeaderLabels(["설비", "교체", "정밀점검", "단순점검"])

        # 예시 데이터 추가
        sample_data = [
            ["Sub_System1", "0.01", "10.26", "100,000,000"],
            ["Sub_System2", "0.01", "10.26", "100,000,000"],
            ["Sub_System3", "0.01", "10.26", "100,000,000"],
            ["Sub_System4", "0.01", "10.26", "100,000,000"],
            ["Sub_System5", "0.01", "10.26", "100,000,000"],
            ["Sub_System6", "0.01", "10.26", "100,000,000"],
            ["Sub_System7", "0.01", "10.26", "100,000,000"],
            ["Sub_System8", "0.01", "10.26", "100,000,000"]
        ]

        for i, row_data in enumerate(sample_data):
            for j, text in enumerate(row_data):
                self.data_table.setItem(i, j, QTableWidgetItem(text))

        self.data_table.resizeColumnsToContents()
        self.main_layout.addWidget(self.data_table)

    def create_buttons(self):
        # 버튼 레이아웃
        button_layout = QHBoxLayout()

        # 저장 버튼
        self.save_button = QPushButton("설정 저장")
        self.save_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-size: 14px;")
        self.save_button.clicked.connect(self.save_current_config)
        button_layout.addWidget(self.save_button)

        # 풀이 버튼
        self.solve_button = QPushButton("풀이")
        self.solve_button.setStyleSheet("background-color: #0066cc; color: white; padding: 10px; font-size: 14px;")
        self.solve_button.clicked.connect(self.solve_problem)
        button_layout.addWidget(self.solve_button)

        self.main_layout.addLayout(button_layout)

    def create_result_section(self):
        # 결과 섹션
        result_label = QLabel("결과")
        result_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.main_layout.addWidget(result_label)

        self.result_table = QTableWidget(9, 5)
        self.result_table.setHorizontalHeaderLabels(["설비", "고장", "정밀점검", "보통점검", "현상유지"])

        # 예시 설비명 추가
        for i in range(9):
            self.result_table.setItem(i, 0, QTableWidgetItem(f"Sub_System{i+1}"))

        self.result_table.resizeColumnsToContents()
        self.main_layout.addWidget(self.result_table)

    def update_constraint_visibility(self):
        # 문제 유형에 따라 UI 요소 표시/숨김
        is_cost_constraint = self.problem_type_combo.currentText() == "비용 제약"

        # 비용 제약 관련 UI 요소
        self.cost_constraint_label.setVisible(is_cost_constraint)
        self.cost_constraint_input.setVisible(is_cost_constraint)

        # 민감도 가중치 관련 UI 요소 (비용 제약일 때만 표시)
        self.sensitivity_weights_label.setVisible(is_cost_constraint)
        for weight_input in self.sensitivity_weights:
            weight_input.setVisible(is_cost_constraint)

        # 민감도 제약 관련 UI 요소 (민감도 제약일 때만 표시)
        self.sensitivity_constraint_frame.setVisible(not is_cost_constraint)

        # 레이아웃 업데이트
        self.adjustSize()

    def update_import_section(self):
        """라디오 버튼 선택에 따라 입력 섹션 업데이트"""
        is_sensitivity = self.sensitivity_radio.isChecked()
        self.sensitivity_frame.setVisible(is_sensitivity)
        self.cost_frame.setVisible(not is_sensitivity)

    def apply_config_to_ui(self):
        """config 설정을 UI 컨트롤에 적용합니다."""
        # 솔버 설정
        solver_config = self.config.get("solver", {})
        solver_type = solver_config.get("type", "SCIP")
        problem_type = solver_config.get("problem_type", "cost_constraint")

        # 콤보박스 설정
        index = self.solver_combo.findText(solver_type)
        if index >= 0:
            self.solver_combo.setCurrentIndex(index)

        index = self.problem_type_combo.findText("비용 제약" if problem_type == "cost_constraint" else "민감도 제약")
        if index >= 0:
            self.problem_type_combo.setCurrentIndex(index)

        # 비용 제약 설정
        self.cost_constraint_input.setText(str(solver_config.get("cost_constraint", 1000)))

        # 가중치 설정
        value_weights = solver_config.get("value_weights", [1.0, 1.0, 1.0])
        for i, weight in enumerate(value_weights):
            if i < len(self.sensitivity_weights):
                self.sensitivity_weights[i].setText(str(weight))

        # 민감도 제약 설정
        reliability_constraint = solver_config.get("reliability_constraint", [1, 1, 1])
        for i, constraint in enumerate(reliability_constraint):
            if i < len(self.sensitivity_constraints):
                self.sensitivity_constraints[i].setText(str(constraint))

        # 파일 경로 설정
        input_config = self.config.get("input", {})
        self.sensitivity_file_input.setText(input_config.get("file_path", ""))
        self.sensitivity_range_input.setText(input_config.get("value_range", ""))
        self.cost_file_input.setText(input_config.get("file_path", ""))
        self.cost_range_input.setText(input_config.get("cost_range", ""))

        input_config = self.config.get("input", {})
        self.add_nothing_checkbox.setChecked(input_config.get("add_nothing_strategy", True))

        output_config = self.config.get("output", {})
        self.output_file_input.setText(output_config.get("file_path", "data/solution.xlsx"))
        self.output_sheet_input.setText(output_config.get("sheet_name", "scip_cost_constraint"))

    def save_current_config(self):
        """현재 UI 설정을 config.json 파일에 저장합니다."""
        # 설정값 가져오기
        solver_type = self.solver_combo.currentText()
        problem_type = "cost_constraint" if self.problem_type_combo.currentText() == "비용 제약" else "reliability_constraint"

        # 설정 업데이트
        self.config["solver"]["type"] = solver_type
        self.config["solver"]["problem_type"] = problem_type

        # 문제 유형에 따라 다른 설정 저장
        if problem_type == "cost_constraint":
            self.config["solver"]["cost_constraint"] = float(self.cost_constraint_input.text())
            self.config["solver"]["value_weights"] = [float(w.text()) for w in self.sensitivity_weights]
        else:
            self.config["solver"]["reliability_constraint"] = [float(c.text()) for c in self.sensitivity_constraints]

        # 입력 파일 경로 저장
        if self.sensitivity_radio.isChecked():
            self.config["input"]["file_path"] = self.sensitivity_file_input.text()
            self.config["input"]["value_range"] = self.sensitivity_range_input.text()
        else:
            self.config["input"]["file_path"] = self.cost_file_input.text()
            self.config["input"]["cost_range"] = self.cost_range_input.text()

        self.config["input"]["add_nothing_strategy"] = self.add_nothing_checkbox.isChecked()

        self.config["output"]["file_path"] = self.output_file_input.text()
        self.config["output"]["sheet_name"] = self.output_sheet_input.text()

        # 설정 저장
        success = save_config(self.config)
        if success:
            QMessageBox.information(self, "설정 저장", "설정이 config.json 파일에 저장되었습니다.")
        else:
            QMessageBox.warning(self, "저장 실패", "설정 저장에 실패했습니다.")

    def load_data(self, data_type):
        """데이터 불러오기 구현 - openpyxl 사용"""
        try:
            if data_type == "sensitivity":
                file_path = self.sensitivity_file_input.text()
                cell_range = self.sensitivity_range_input.text()
                sheet_name = self.config["input"]["value_sheet"]
            else:  # cost
                file_path = self.cost_file_input.text()
                cell_range = self.cost_range_input.text()
                sheet_name = self.config["input"]["cost_sheet"]

            # 엑셀 파일 열기
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            sheet = workbook[sheet_name]

            # 셀 범위 파싱 (예: "A1:D10")
            if cell_range:
                start_cell, end_cell = cell_range.split(":")
                start_col, start_row = coordinate_from_string(start_cell)
                end_col, end_row = coordinate_from_string(end_cell)

                start_col_idx = column_index_from_string(start_col)
                end_col_idx = column_index_from_string(end_col)
            else:
                # 범위가 지정되지 않은 경우 전체 데이터 영역 사용
                start_row, start_col_idx = 1, 1
                end_row = sheet.max_row
                end_col_idx = sheet.max_column

            # 헤더 추출 (첫 번째 행)
            headers = []
            for col in range(start_col_idx, end_col_idx + 1):
                cell_value = sheet.cell(start_row, col).value
                headers.append(str(cell_value) if cell_value is not None else f"Column {col}")

            # 테이블 설정 (헤더 제외한 데이터 행)
            row_count = end_row - start_row
            col_count = end_col_idx - start_col_idx + 1
            self.data_table.setRowCount(row_count)
            self.data_table.setColumnCount(col_count)
            self.data_table.setHorizontalHeaderLabels(headers)

            # 데이터 채우기 (헤더 행 제외)
            for row in range(start_row + 1, end_row + 1):
                table_row = row - start_row - 1
                for col in range(start_col_idx, end_col_idx + 1):
                    table_col = col - start_col_idx
                    value = sheet.cell(row, col).value
                    cell_value = str(value) if value is not None else ""
                    self.data_table.setItem(table_row, table_col, QTableWidgetItem(cell_value))

            self.data_table.resizeColumnsToContents()

            # 설정 업데이트
            if data_type == "sensitivity":
                self.config["input"]["file_path"] = file_path
                self.config["input"]["value_sheet"] = sheet_name
                self.config["input"]["value_range"] = cell_range
            else:
                self.config["input"]["file_path"] = file_path
                self.config["input"]["cost_sheet"] = sheet_name
                self.config["input"]["cost_range"] = cell_range

        except Exception as e:
            QMessageBox.critical(self, "오류", f"데이터 로드 오류: {e}")
            print(f"데이터 로드 오류: {e}")

    def solve_problem(self):
        # 현재 설정 저장
        self.save_current_config()

        try:
            # 문제를 읽고 풀기
            self.problem = read_problem_from_excel(
                self.config["input"]["file_path"],
                cost_range=self.config["input"]["cost_range"],
                cost_sheet=self.config["input"]["cost_sheet"],
                value_range=self.config["input"]["value_range"],
                value_sheet=self.config["input"]["value_sheet"]
            )

            allow_nothing_strategy = not self.config["input"]["add_nothing_strategy"]

            if self.config["input"]["add_nothing_strategy"]:
                self.problem = add_nothing_strategy(self.problem)

            # 솔버 설정
            solver_type = self.config["solver"]["type"]
            problem_type = self.config["solver"]["problem_type"]

            # 솔버 실행
            if solver_type == "SCIP":
                if problem_type == "cost_constraint":
                    self.solution, cost, value, time = scip.solve_cost_constraint(
                        self.problem,
                        cost_constraint=self.config["solver"]["cost_constraint"],
                        value_weights=self.config["solver"]["value_weights"],
                        allow_zero_strategy=allow_nothing_strategy
                    )
                else:
                    self.solution, cost, value, time = scip.solve_reliability_constraint(
                        self.problem,
                        reliability_constraint=self.config["solver"]["reliability_constraint"],
                        allow_zero_strategy=allow_nothing_strategy
                    )
            else:  # CP-SAT
                if problem_type == "cost_constraint":
                    self.solution, cost, value, time = cpsat.solve_cost_constraint(
                        self.problem,
                        cost_constraint=self.config["solver"]["cost_constraint"],
                        value_weights=self.config["solver"]["value_weights"],
                        allow_zero_strategy=allow_nothing_strategy
                    )
                else:
                    self.solution, cost, value, time = cpsat.solve_reliability_constraint(
                        self.problem,
                        reliability_constraint=self.config["solver"]["reliability_constraint"],
                        allow_zero_strategy=allow_nothing_strategy
                    )

            # 결과 표시
            self.display_solution()

            # 결과 저장
            write_solution_to_excel(
                self.config["output"]["file_path"],
                sheet_name=self.config["output"]["sheet_name"],
                problem=self.problem,
                solution=self.solution
            )

            QMessageBox.information(self, "계산 완료",
                                    f"최적화 계산이 완료되었습니다.\n"
                                    f"총 비용: {cost}\n"
                                    f"계산 시간: {time:.2f}초\n"
                                    f"결과가 {self.config['output']['file_path']} 파일에 저장되었습니다.")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"최적화 문제 해결 오류: {e}")
            print(f"최적화 문제 해결 오류: {e}")

    def display_solution(self):
        if not self.solution or not self.problem:
            return

        # 결과 테이블 설정
        costs = self.problem["cost"]
        values = self.problem["value"]

        # 결과 테이블 크기 설정
        self.result_table.setRowCount(len(self.solution))
        self.result_table.setColumnCount(5)  # 설비, 변경, 정밀점검, 보통점검, 현상유지
        self.result_table.setHorizontalHeaderLabels(["설비", "변경", "정밀점검", "보통점검", "현상유지"])

        # 결과 채우기
        for i, choice in enumerate(self.solution):
            # 설비명
            item_name = costs.index[i] if i < len(costs.index) else f"Item {i}"
            self.result_table.setItem(i, 0, QTableWidgetItem(str(item_name)))

            # 선택된 전략 표시
            # 현상유지 상태 확인 (choice가 0, 1, 2 이외의 값인 경우)
            is_maintained = choice not in [0, 1, 2] or choice is None

            for j in range(1, self.result_table.columnCount()):
                if is_maintained and j == 4:  # 현상유지 열 (인덱스 4)
                    self.result_table.setItem(i, j, QTableWidgetItem("✓"))
                    self.result_table.item(i, j).setTextAlignment(Qt.AlignCenter)
                elif not is_maintained and j - 1 == choice:  # 변경(1), 정밀점검(2), 보통점검(3) 열
                    self.result_table.setItem(i, j, QTableWidgetItem("✓"))
                    self.result_table.item(i, j).setTextAlignment(Qt.AlignCenter)
                else:
                    self.result_table.setItem(i, j, QTableWidgetItem(""))

        self.result_table.resizeColumnsToContents()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OptimizationUI()
    window.show()
    sys.exit(app.exec())