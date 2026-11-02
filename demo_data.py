"""純屬虛構的家庭收支、股票價格與持倉；並非市場報價。"""

DEMO_BUDGET = [
    {"kind": "收入", "category": "家庭成員甲薪金", "amount": 36000.0},
    {"kind": "收入", "category": "家庭成員乙薪金", "amount": 22000.0},
    {"kind": "收入", "category": "兼職收入", "amount": 2000.0},
    {"kind": "支出", "category": "住屋", "amount": 16000.0},
    {"kind": "支出", "category": "飲食及日用品", "amount": 8000.0},
    {"kind": "支出", "category": "交通", "amount": 2400.0},
    {"kind": "支出", "category": "水電及通訊", "amount": 1800.0},
    {"kind": "支出", "category": "保險及醫療", "amount": 3000.0},
    {"kind": "支出", "category": "子女教育", "amount": 4500.0},
    {"kind": "支出", "category": "休閒及其他", "amount": 4100.0},
]

DEMO_HOLDINGS = [
    {"symbol": "0700.HK", "name": "示範科技甲", "currency": "HKD", "quantity": 100.0, "avg_cost": 320.0, "price": 350.0},
    {"symbol": "0005.HK", "name": "示範銀行乙", "currency": "HKD", "quantity": 400.0, "avg_cost": 65.0, "price": 62.0},
    {"symbol": "AAPL", "name": "示範科技丙", "currency": "USD", "quantity": 20.0, "avg_cost": 180.0, "price": 195.0},
    {"symbol": "VOO", "name": "示範指數基金", "currency": "USD", "quantity": 10.0, "avg_cost": 450.0, "price": 470.0},
]
