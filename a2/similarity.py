import numpy as np

a = np.array([3, 4])
b = np.array([4, 3])
print("내적 a와 b:", a @ b)

c = np.array([-4, 3])
d = np.array([6, 8])
print("내적 a와 c:", a @ c, "  a와 d:", a @ d)
print("길이 a:", np.linalg.norm(a), "  d:", np.linalg.norm(d))


def cosine(x, y):
    return x @ y / (np.linalg.norm(x) * np.linalg.norm(y))  # 내적 ÷ (길이 × 길이)


print("코사인 a와 b:", round(cosine(a, b), 2), "  a와 c:", round(cosine(a, c), 2), "  a와 d:", round(cosine(a, d), 2))
print("거리 a와 b:", round(np.linalg.norm(a - b), 2), "  a와 c:", round(np.linalg.norm(a - c), 2))
an, dn = a / np.linalg.norm(a), d / np.linalg.norm(d)  # 길이를 1로 맞춘다(정규화)
print("정규화 a:", an, "  d:", dn)
print("정규화 뒤 내적 a와 d:", round(an @ dn, 2), "  길이:", np.linalg.norm(an))
