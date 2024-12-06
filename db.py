import sqlite3

def create_empty_db():
    """
    Tạo cơ sở dữ liệu với bảng slot_info, sử dụng user_id làm khóa chính.
    """
    conn = sqlite3.connect('slots.db')
    cursor = conn.cursor()

    # Tạo bảng với user_id là khóa chính
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS slot_info (
        user_id TEXT PRIMARY KEY,              -- user_id là khóa chính
        type TEXT,                             -- Cột type
        length TEXT,                           -- Cột length
        width TEXT,                            -- Cột width
        height TEXT,                           -- Cột height
        weight TEXT,                           -- Cột weight
        address TEXT                           -- Cột address
    )
    ''')

    conn.commit()
    conn.close()

create_empty_db()


def get_first_row_column_values():
    # Kết nối tới cơ sở dữ liệu
    conn = sqlite3.connect('slots.db')
    cursor = conn.cursor()

    # Thực hiện câu lệnh PRAGMA để lấy thông tin về các cột trong bảng
    cursor.execute('PRAGMA table_info(slot_info);')
    columns = cursor.fetchall()

    # Lấy danh sách tên cột
    column_names = [column[1] for column in columns]

    # Truy vấn lấy dòng đầu tiên trong bảng
    cursor.execute('SELECT * FROM slot_info LIMIT 1;')
    row = cursor.fetchone()
    # Dictionary lưu trữ tên cột và giá trị tương ứng trong dòng đầu tiên
    column_values = {}

    if row:
        for i, value in enumerate(row):
            column_values[column_names[i]] = value

    # Đóng kết nối
    conn.close()

    return column_values

# Gọi hàm và in ra dictionary các cột và giá trị trong dòng đầu tiên
column_values = get_first_row_column_values()

print(column_values)
#
# import sqlite3
#
#
# def insert_or_update_slot(user_id, column, value):
#     """
#     Thêm hoặc cập nhật thông tin trong bảng slot_info dựa trên user_id.
#
#     Args:
#     - user_id (str): ID của người dùng, là khóa chính.
#     - column (str): Tên cột muốn cập nhật.
#     - value (str): Giá trị mới của cột.
#     """
#     conn = sqlite3.connect('slots.db')
#     cursor = conn.cursor()
#
#     # Kiểm tra nếu user_id đã tồn tại trong bảng
#     cursor.execute("SELECT 1 FROM slot_info WHERE user_id = ?", (user_id,))
#     exists = cursor.fetchone()
#
#     if exists:
#         # Nếu user_id đã tồn tại, cập nhật giá trị của cột được chỉ định
#         cursor.execute(f"UPDATE slot_info SET {column} = ? WHERE user_id = ?", (value, user_id))
#         print(f"Cập nhật: user_id {user_id}, {column} = {value}")
#     else:
#         # Nếu user_id chưa tồn tại, chèn một dòng mới với user_id và giá trị của cột được chỉ định
#         cursor.execute(f"INSERT INTO slot_info (user_id, {column}) VALUES (?, ?)", (user_id, value))
#         print(f"Thêm mới: user_id {user_id}, {column} = {value}")
#
#     conn.commit()
#     conn.close()
# insert_or_update_slot("user123", "type", "nhà thép")

def get_row_by_user_id( user_id):
    """
    Lấy giá trị của các cột trong dòng tương ứng với user_id.

    Args:
    - user_id (str): ID của người dùng cần tìm.

    Returns:
    - dict: Dictionary chứa tên cột và giá trị tương ứng, hoặc None nếu không tìm thấy.
    """
    # Kết nối tới cơ sở dữ liệu
    conn = sqlite3.connect('slots.db')
    cursor = conn.cursor()

    try:
        # Lấy danh sách tên cột trong bảng
        cursor.execute('PRAGMA table_info(slot_info);')
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]

        # Truy vấn để lấy dòng dựa trên user_id
        cursor.execute('SELECT * FROM slot_info WHERE user_id = ?;', (user_id,))
        row = cursor.fetchone()

        # Dictionary lưu trữ tên cột và giá trị tương ứng
        column_values = {}

        if row:
            for i, value in enumerate(row):
                column_values[column_names[i]] = value

        return column_values if row else None
    finally:
        # Đóng kết nối
        conn.close()
result = get_row_by_user_id("6835734916")

if result:
    print("Dữ liệu của user123:", result)
else:
    print("Không tìm thấy user_id user123")

