def process_solution(selected:list[list[int]]):
    """
    선택된 전략을 처리하여 최종 결과를 반환합니다.
    Zero Strategy를 허용하는 경우, 선택된 전략이 없을 때 -1로 표시합니다.

    Args:
        selected (list[list[int]]): 선택된 전략 리스트 one-hot 인코딩 형태

    Returns:
        list[int]: 최종 선택된 전략, 각 아이템에 대해 선택된 전략의 인덱스
    """
    return [selected[i].index(1) if 1 in selected[i] else -1 for i in range(len(selected))]
