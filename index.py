import tkinter as tk
from tkinter import messagebox, filedialog
import sqlite3
import os
import shutil

# Veritabanı bağlantısı oluştur
conn = sqlite3.connect('user_data.db')
c = conn.cursor()

# Eğer tablo yoksa tablo oluştur
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        owner TEXT NOT NULL
    )
''')
conn.commit()

# Admin kullanıcısını ekle
def create_admin():
    admin_username = "admin"
    admin_password = "admin123"
    
    c.execute('SELECT * FROM users WHERE username=?', (admin_username,))
    if not c.fetchone():
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (admin_username, admin_password))
        conn.commit()

# Kayıt fonksiyonu
def register():
    username = username_entry.get()
    password = password_entry.get()
    
    if username and password:
        c.execute('SELECT * FROM users WHERE username=?', (username,))
        if c.fetchone():
            messagebox.showwarning("Uyarı", "Bu kullanıcı adı zaten alınmış!")
        else:
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            messagebox.showinfo("Başarılı", "Kayıt başarılı!")
            show_main_menu()  # Kayıt tamamlandıktan sonra anasayfaya dön
    else:
        messagebox.showwarning("Uyarı", "Lütfen kullanıcı adı ve şifre giriniz!")

# Giriş fonksiyonu
def login():
    global current_user
    username = username_entry.get()
    password = password_entry.get()
    
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    result = c.fetchone()
    
    if result:
        current_user = username
        messagebox.showinfo("Başarılı", "Giriş başarılı!")
        login_frame.pack_forget()  # Giriş ekranını kapat
        show_main_menu()  # Anasayfaya yönlendir
    else:
        messagebox.showwarning("Hata", "Kullanıcı adı veya şifre yanlış!")

# Dosya ekleme fonksiyonu
def upload_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        filename = os.path.basename(file_path)
        new_path = os.path.join("uploads", filename)
        os.makedirs("uploads", exist_ok=True)
        shutil.copy2(file_path, new_path)
        c.execute('INSERT INTO files (filename, filepath, owner) VALUES (?, ?, ?)', (filename, new_path, current_user))
        conn.commit()
        messagebox.showinfo("Başarılı", "Dosya yüklendi!")
        show_main_menu()  # Dosya yüklendikten sonra anasayfaya dön

# Dosya listeleme fonksiyonu
def list_files():
    files_window = tk.Toplevel(file_operations_window)
    files_window.title("Dosya Listesi")
    files_window.geometry("300x200")
    
    c.execute('SELECT id, filename, owner FROM files WHERE owner=?', (current_user,))
    files = c.fetchall()
    
    for file in files:
        file_id = file[0]
        filename = file[1]
        owner = file[2]

        file_label = tk.Label(files_window, text=f"{filename} - {owner}")
        file_label.pack()

        file_label.bind("<Button-3>", lambda event, fid=file_id: show_context_menu(event, fid))

# Sağ tıklama menüsü
def show_context_menu(event, file_id):
    context_menu = tk.Menu(root, tearoff=0)
    context_menu.add_command(label="Dosyayı İndir", command=lambda: download_file(file_id))
    context_menu.add_command(label="Dosyayı Paylaş", command=lambda: share_file(file_id))
    context_menu.tk_popup(event.x_root, event.y_root)

# Dosya indirme fonksiyonu
def download_file(file_id):
    c.execute('SELECT filename, filepath FROM files WHERE id=?', (file_id,))
    result = c.fetchone()
    if result:
        filename, filepath = result
        ext = os.path.splitext(filename)[1]  # Dosya uzantısını al
        destination = filedialog.asksaveasfilename(defaultextension=ext, initialfile=filename)
        if destination:
            shutil.copy2(filepath, destination)
            messagebox.showinfo("Başarılı", "Dosya indirildi!")
            show_main_menu()  # Dosya indirildikten sonra anasayfaya dön

# Dosya paylaşma fonksiyonu
def share_file(file_id):
    global share_window, share_file_id, username_entry
    share_file_id = file_id
    share_window = tk.Toplevel(root)
    share_window.title("Dosya Paylaş")
    share_window.geometry("300x100")

    tk.Label(share_window, text="Paylaşmak istediğiniz kullanıcı adını girin:").pack()
    username_entry = tk.Entry(share_window)
    username_entry.pack()
    tk.Button(share_window, text="Paylaş", command=share).pack()

def share():
    username = username_entry.get()
    c.execute('SELECT * FROM users WHERE username=?', (username,))
    if c.fetchone():
        c.execute('UPDATE files SET owner=? WHERE id=?', (username, share_file_id))
        conn.commit()
        messagebox.showinfo("Başarılı", "Dosya paylaşıldı!")
        share_window.destroy()
        show_main_menu()  # Dosya paylaşıldıktan sonra anasayfaya dön
    else:
        messagebox.showwarning("Hata", "Kullanıcı bulunamadı!")

# Dosya silme fonksiyonu
def delete_file():
    files_window = tk.Toplevel(file_operations_window)
    files_window.title("Dosya Sil")
    files_window.geometry("300x200")
    
    c.execute('SELECT id, filename FROM files WHERE owner=?', (current_user,))
    files = c.fetchall()
    
    for file in files:
        file_id = file[0]
        filename = file[1]
        tk.Button(files_window, text=filename, command=lambda fid=file_id: confirm_delete(fid)).pack()

def confirm_delete(file_id):
    c.execute('SELECT filepath FROM files WHERE id=?', (file_id,))
    file = c.fetchone()
    if file:
        os.remove(file[0])
        c.execute('DELETE FROM files WHERE id=?', (file_id,))
        conn.commit()
        messagebox.showinfo("Başarılı", "Dosya silindi!")
        show_main_menu()  # Dosya silindikten sonra anasayfaya dön

# Dosya işlemleri penceresini gösteren fonksiyon
def show_file_operations():
    global file_operations_window
    file_operations_window = tk.Toplevel(root)
    file_operations_window.title("Dosya İşlemleri")
    file_operations_window.geometry("300x300")
    
    tk.Button(file_operations_window, text="Dosya Ekle", command=upload_file).pack(pady=5)
    tk.Button(file_operations_window, text="Dosyaları Listele", command=list_files).pack(pady=5)
    
    if current_user == "admin":
        tk.Button(file_operations_window, text="Dosya Sil", command=delete_file).pack(pady=5)

    tk.Button(file_operations_window, text="Kapat", command=file_operations_window.destroy).pack(pady=5)

# Ana menüyü gösteren fonksiyon
def show_main_menu(prev_frame=None):
    if prev_frame:
        prev_frame.pack_forget()
    
    main_menu = tk.Frame(root)
    main_menu.pack()
    
    tk.Button(main_menu, text="Dosya İşlemleri", command=show_file_operations).pack(pady=5)

# Ana pencere oluştur
root = tk.Tk()
root.title("Kullanıcı Girişi")
root.geometry("300x200")

current_user = None

# Kullanıcı adı etiketi ve giriş alanı
login_frame = tk.Frame(root)
login_frame.pack(pady=20)

tk.Label(login_frame, text="Kullanıcı Adı:").pack()
username_entry = tk.Entry(login_frame)
username_entry.pack()

# Şifre etiketi ve giriş alanı
tk.Label(login_frame, text="Şifre:").pack()
password_entry = tk.Entry(login_frame, show="*")
password_entry.pack()

# Kayıt Ol butonu
register_button = tk.Button(login_frame, text="Kayıt Ol", command=register)
register_button.pack(pady=5)

# Giriş Yap butonu
login_button = tk.Button(login_frame, text="Giriş Yap", command=login)
login_button.pack(pady=5)

# Admin kullanıcısını oluştur
create_admin()

# Uygulamayı başlat
root.mainloop()

# Veritabanı bağlantısnı kapat
conn.close()