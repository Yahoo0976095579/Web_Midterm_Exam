import sqlite3
# 設定常數
DB_NAME = 'bookstore.db'
CHOICE_OPTIONS = ["1", "2", "3", "4", "5"]  # 可選擇的操作項目
SALE_DATE = "YYYY-MM-DD"  # 銷售日期格式
SQTY_MIN = 1  # 購買數量最小值
DISCOUNT_MIN = 0  # 折扣金額最小值



def initialize_db(conn: sqlite3.Connection) -> None:
    #初始化資料庫表格和資料
    cursor = conn.cursor()  #建立cursor物件
    try:
        #建立member資料表
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS member (
            mid TEXT PRIMARY KEY,
            mname TEXT NOT NULL,
            mphone TEXT NOT NULL,
            memail TEXT
            );
            INSERT INTO member VALUES ('M001', 'Alice', '0912-345678', 'alice@example.com');
            INSERT INTO member VALUES ('M002', 'Bob', '0923-456789', 'bob@example.com');
            INSERT INTO member VALUES ('M003', 'Cathy', '0934-567890', 'cathy@example.com');
        """)
        #建立書籍資料表
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS book (
            bid TEXT PRIMARY KEY,
            btitle TEXT NOT NULL,
            bprice INTEGER NOT NULL,
            bstock INTEGER NOT NULL
            );
            INSERT INTO book VALUES ('B001', 'Python Programming', 600, 50);
            INSERT INTO book VALUES ('B002', 'Data Science Basics', 800, 30);
            INSERT INTO book VALUES ('B003', 'Machine Learning Guide', 1200, 20);
        """)
        #建立已銷售書籍資料表
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS sale (
            sid INTEGER PRIMARY KEY AUTOINCREMENT,
            sdate TEXT NOT NULL, -- 格式為 'YYYY-MM-DD'
            mid TEXT NOT NULL,
            bid TEXT NOT NULL,
            sqty INTEGER NOT NULL,      -- 數量
            sdiscount INTEGER NOT NULL, -- 折扣金額，單位為元
            stotal INTEGER NOT NULL     -- 總額 = (書本單價 × 數量) - 折扣
            );                  
            INSERT INTO sale (sdate, mid, bid, sqty, sdiscount, stotal) VALUES ('2024-01-15', 'M001', 'B001', 2, 100, 1100);
            INSERT INTO sale (sdate, mid, bid, sqty, sdiscount, stotal) VALUES ('2024-01-16', 'M002', 'B002', 1, 50, 750);
            INSERT INTO sale (sdate, mid, bid, sqty, sdiscount, stotal) VALUES ('2024-01-17', 'M001', 'B003', 3, 200, 3400);
            INSERT INTO sale (sdate, mid, bid, sqty, sdiscount, stotal) VALUES ('2024-01-18', 'M003', 'B001', 1, 0, 600);
        """)
        conn.commit()  # 寫入資料庫
    except sqlite3.Error as e:
        print(f"=> 錯誤：初始化資料庫失敗，錯誤訊息: {e}")
        conn.rollback()  # 回復交易

#主選單界面
def display_menu() -> None:
    print("***************選單***************")
    print("1. 新增銷售紀錄")
    print("2. 顯示銷售報表")
    print("3. 更新銷售紀錄")
    print("4. 刪除銷售紀錄")
    print("5. 離開")
    print("**********************************")


#獲取操作項目
def get_user_choice() -> str:
    while True:
        choice = input("請選擇操作項目(Enter 離開)：")
        if choice == "":
            return CHOICE_OPTIONS[4]  # 按 Enter視為選擇離開
        elif choice in CHOICE_OPTIONS:
            print(" ")
            return choice
        else:
            print("=> 請輸入有效的選項（1-5）")
            display_menu()  # 重新顯示選單


#新增銷售紀錄
def add_sale(conn: sqlite3.Connection) -> None:
    """新增銷售紀錄
    
        conn: 資料庫連線物件
        
    處理流程:
        1. 驗證銷售日期格式
        2. 驗證會員編號和書籍編號
        3. 驗證購買數量和折扣金額
        4. 檢查庫存是否足夠
        5. 新增銷售紀錄並更新庫存
    """
    cursor = conn.cursor()
    while True:
        sale_sdate = input(f"請輸入銷售日期({SALE_DATE})：")
        if len(sale_sdate) == 10 and sale_sdate[4] == '-' and sale_sdate[7] == '-':
            break  # 日期格式正確，跳出迴圈
        else:
            print("=> 日期格式錯誤，請重新輸入")

    mid = input("請輸入會員編號：")
    bid = input("請輸入書籍編號：")

    sqty = sqty_discount_int("請輸入購買數量：")
    while sqty < SQTY_MIN:
        print("=> 錯誤：數量必須為正整數，請重新輸入")
        sqty = sqty_discount_int("請輸入購買數量：")

    discount = sqty_discount_int("請輸入折扣金額：")
    while discount < DISCOUNT_MIN:
        print("=> 錯誤：折扣金額不能為負數，請重新輸入")
        discount = sqty_discount_int("請輸入折扣金額：")
    try:
        #從資料庫找有沒有這個id，沒有就回傳NONE，有就太好了
        cursor.execute("SELECT mid FROM member WHERE mid = ?", (mid.upper(),))
        data_mid = cursor.fetchone()
    except sqlite3.Error as e:
        print(f"=> 錯誤：查詢會員編號失敗，錯誤訊息: {e}")
        return
    try:
        cursor.execute("SELECT bid, bstock,bprice FROM book WHERE bid = ?", (bid.upper(),))
        data_book = cursor.fetchone()
    except sqlite3.Error as e:
        print(f"=> 錯誤：查詢書籍編號失敗，錯誤訊息: {e}")
        return

    stotal = (data_book['bprice'] * int(sqty)) - int(discount)  # 計算總額

    if data_book is None or data_mid is None:
        print("=> 錯誤：會員編號或書籍編號無效")
    elif data_book['bstock'] < sqty:
        print(f"=> 錯誤：書籍庫存不足 (現有庫存: {data_book['bstock']})")#查詢指定的書籍編號庫存是否足夠購買的數量
    else:
        #老師要求的交易管理
        try:
            cursor.execute("""
                INSERT INTO sale (sdate, mid, bid, sqty, sdiscount, stotal) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sale_sdate, mid.upper(), bid.upper(), sqty, discount, stotal))

                # 更新書籍庫存，原本的剩餘書籍-購買的數量
            cursor.execute("UPDATE book SET bstock = bstock - ? WHERE bid = ? ", (sqty, bid.upper()))

            print(f"銷售記錄已新增！(銷售總額: {stotal})")
            conn.commit()  # 寫入資料庫
        except sqlite3.Error as e:
            conn.rollback()  # 回復交易
            print(f"=> 錯誤：新增銷售記錄失敗，錯誤訊息: {e}")

def show_sale(conn: sqlite3.Connection) -> None:
    """顯示銷售報表
    使用 sqlite3.Row 使查詢結果可以用欄位名稱存取，嚴格遵守老師的要求
        conn: 資料庫連線物件
    查詢並顯示所有銷售報表，按銷售編號排序。
    """
    cursor = conn.cursor()
    print("==================== 銷售報表 ====================")
    try:
        cursor.execute("""
                SELECT s.sid, s.sdate, m.mname, b.btitle, b.bprice, s.sqty, s.sdiscount, s.stotal FROM sale s
                INNER JOIN MEMBER m on m.mid = s.mid
                INNER JOIN BOOK b on b.bid = s.bid
                ORDER BY s.sid

        """)
        data = cursor.fetchall()  # 取得所有資料
    except sqlite3.Error as e:
        print(f"=> 錯誤：查詢銷售報表失敗，錯誤訊息: {e}")
        return
    
    for row in data:
        print(f"銷售: #{row['sid']}")
        print(f"銷售編號: {row['sid']}")
        print(f"銷售日期: {row['sdate']}")
        print(f"會員姓名: {row['mname']}")
        print(f"書籍標題: {row['btitle']}")
        print("--------------------------------------------------")
        print("單價\t數量\t折扣\t小計")
        print("--------------------------------------------------")
        print(f"{row['bprice']:,}\t{row['sqty']}\t{row['sdiscount']:,}\t{row['stotal']:,}")
        print("--------------------------------------------------")
        print(f"銷售總額: {row['stotal']:,}")
        print("==================================================")
        print(" ")

def update_sale(conn: sqlite3.Connection) -> None:
    """更新銷售紀錄的折扣金額
    使用 sqlite3.Row 使查詢結果可以用欄位名稱存取，嚴格遵守老師的要求
        conn: 資料庫連線物件

    處理流程:
        1. 顯示銷售記錄列表
        2. 驗證銷售編號是否存在
        3. 驗證折扣金額是否為正整數
        4. 更新銷售紀錄的折扣金額和總額
    """
    cursor = conn.cursor()
    sale_list(conn)  # 顯示銷售記錄列表
    sale_id = update_delete_int("請選擇要更新的銷售編號 (輸入數字或按 Enter 取消): ")
    if sale_id == "":
        print(" ")
        return
    try:
        while True:
            cursor.execute("SELECT sid FROM sale WHERE sid = ?", (sale_id,))
            sales = cursor.fetchone()
            if sales is not None:
                break
            print("=> 錯誤：請輸入有效的銷售編號")
            sale_id = update_delete_int("請選擇要更新的銷售編號 (輸入數字或按 Enter 取消): ")
    except sqlite3.Error as e:
        print(f"=> 錯誤：查詢銷售編號失敗，錯誤訊息: {e}")
        return
    

    update_sale_discount = discount_int("請輸入新的折扣金額：")
    while update_sale_discount < 0:
        print("=> 錯誤：折扣金額不能為負數，請重新輸入")
        update_sale_discount = discount_int("請輸入新的折扣金額：")
    
    try:
        cursor.execute("SELECT stotal, sdiscount FROM sale WHERE sid = ?", (sale_id,))
        data_new_stotal = cursor.fetchone()
    except sqlite3.Error as e:
        print(f"=> 錯誤：查詢銷售編號失敗，錯誤訊息: {e}")
        return
    new_stotal = data_new_stotal['stotal'] + data_new_stotal['sdiscount'] - update_sale_discount
    try:
        cursor.execute("UPDATE sale SET sdiscount = ?, stotal = ? WHERE sid = ?", (update_sale_discount, new_stotal, sale_id))
        conn.commit()  # 寫入資料庫
        print(f"銷售編號 {sale_id} 已更新 ! 銷售總額 {new_stotal}")
    except sqlite3.Error as e:
        conn.rollback()  # 回復交易
        print(f"=> 錯誤：更新銷售記錄失敗，錯誤訊息: {e}")


def delete_sale(conn: sqlite3.Connection) -> None:
    """刪除銷售紀錄
    使用 sqlite3.Row 使查詢結果可以用欄位名稱存取，嚴格遵守老師的要求
        conn: 資料庫連線物件
    處理流程:
        1. 顯示銷售記錄列表
        2. 驗證銷售編號是否存在
        3. 刪除銷售紀錄
    """
    cursor = conn.cursor()
    sale_list(conn)  # 顯示銷售記錄列表
    sale_id = update_delete_int("請選擇要刪除的銷售編號 (輸入數字或按 Enter 取消): ")
    if sale_id == "":
        print(" ")
        return
    try:
        while True:
            cursor.execute("SELECT sid FROM sale WHERE sid = ?", (sale_id,))
            sales = cursor.fetchone()
            if sales is not None:
                break
            print("=> 錯誤：請輸入有效的銷售編號")
            sale_id = update_delete_int("請選擇要刪除的銷售編號 (輸入數字或按 Enter 取消): ")
    except sqlite3.Error as e:
        print(f"=> 錯誤：查詢銷售編號失敗，錯誤訊息: {e}")
        return
    

    try:
        cursor.execute("DELETE FROM sale WHERE sid = ?", (sale_id,))
        conn.commit()  # 寫入資料庫
        print(f"=> 銷售編號 {sale_id} 已刪除")
    except sqlite3.Error as e:
        conn.rollback()  # 回復交易
        print(f"=> 錯誤：刪除銷售記錄失敗，錯誤訊息: {e}")

#數量或折扣使用 try-except ValueError 捕捉非整數輸入
def sqty_discount_int(value) -> int:
    """
    驗證數量或折扣金額是否為正整數
    這個函數會不斷要求使用者輸入，直到輸入的值是正整數為止。
    如果輸入的值不是正整數，則會顯示錯誤訊息並要求重新輸入。

    """
    while True:
        int_input = input(value)
        try:
            return int(int_input)#如果try成功(int)，則返回該數
        except ValueError:
            print("=> 錯誤：數量或折扣必須為整數，請重新輸入")

#折扣使用 try-except ValueError 捕捉非整數輸入
def discount_int(value) -> int:
    """
    驗證折扣金額是否為正整數
    這個函數會不斷要求使用者輸入，直到輸入的值是正整數為止。
    如果輸入的值不是正整數，則會顯示錯誤訊息並要求重新輸入。

    """
    while True:
        int_input = input(value)
        try:
            return int(int_input)#如果try成功(int)，則返回該數
        except ValueError:
            print("=> 錯誤：折扣必須為整數，請重新輸入")

#更新-刪除使用 try-except ValueError 捕捉非整數輸入
def update_delete_int(value) -> int:
    """
    驗證輸入是否為正整數
    這個函數會不斷要求使用者輸入，直到輸入的值是正整數為止。
    如果輸入的值不是正整數，則會顯示錯誤訊息並要求重新輸入。
    """
    while True:
        int_input = input(value)
        try:
            return int(int_input)#如果try成功(int)，則返回該數
        except ValueError:
            print("=> 錯誤：請輸入有效的數字")



def sale_list(conn: sqlite3.Connection) -> None:
    """顯示銷售記錄列表
    使用 sqlite3.Row 使查詢結果可以用欄位名稱存取，嚴格遵守老師的要求
        conn: 資料庫連線物件
    顯示銷售記錄列表，提示使用者輸入要刪除的銷售編號，執行刪除操作並提交到資料庫。
    """
    cursor = conn.cursor()
    print("======== 銷售記錄列表 ========")
    try:
        cursor.execute("""
        SELECT s.sid, m.mname, s.sdate, s.stotal FROM sale s 
            INNER JOIN member m on m.mid = s.mid
        """)
        data = cursor.fetchall()  # 取得所有資料
    except sqlite3.Error as e:
        print(f"=> 錯誤：查詢銷售記錄列表失敗，錯誤訊息: {e}")
        return
    for row in data:
        print(f"{row['sid']}. 銷售編號: {row['sid']} - 會員: {row['mname']} - 日期: {row['sdate']}")

    print("================================")

#主程式
def main()-> None:
    # 使用上下文管理器連線資料庫
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row  # 使查詢結果可以用欄位名稱存取
        initialize_db(conn)  # 初始化資料庫
        while True:
            display_menu()
            choice = get_user_choice()

            if choice == "1":
                add_sale(conn)
            elif choice == "2":
                show_sale(conn)
            elif choice == "3":
                update_sale(conn)
            elif choice == "4":
                delete_sale(conn)
            elif choice == "5":
                print("程式結束。")
                break

if __name__ == "__main__":
    main()

