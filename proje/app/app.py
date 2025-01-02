from flask import Flask, render_template, request, redirect, flash , session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24) 
database_dir = "db.db"

def create_connection():
    return sqlite3.connect(database_dir)

@app.route("/")
def girisEkrani():
    return render_template("index.html", title="Anasayfa")

@app.route("/girisyap", methods=["GET", "POST"])
def girisyap():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        connection = create_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM User WHERE username = ? AND password = ?
        """, (username, password))
        result = cursor.fetchone()

        if result[0] == 0:
            flash("Kullanıcı adı veya şifre yanlış!", "error")
            return redirect("/girisyap")
        else:
            session['username'] = username  
            return redirect("/anasayfa")
    else:  # GET
        return render_template("index.html", title="Giriş Yap")

@app.route("/anasayfa", methods=["GET", "POST"])
def anasayfa():
    connection = create_connection()
    cursor = connection.cursor()

    # Sayfa numarasını al, varsayılan olarak 1
    page = request.args.get("page", 1, type=int)
    items_per_page = 10  # Her sayfada gösterilecek ürün sayısı
    offset = (page - 1) * items_per_page  # Sayfa başına gelen ürün sayısı

    arama = request.args.get("search")  # Arama kontrolü
    if arama:
        cursor.execute("""
            SELECT UPPER(UrunAdi), UPPER(UrunMarkasi), UrunAdedi, UPPER(UrunOzelligi)
            FROM Urunler
            WHERE UrunAdi LIKE ? OR UrunMarkasi LIKE ? OR UrunOzelligi LIKE ?
            LIMIT ? OFFSET ?
        """, ('%' + arama + '%', '%' + arama + '%', '%' + arama + '%', items_per_page, offset))
    else:
        cursor.execute("""
            SELECT UrunID, UPPER(UrunAdi), UPPER(UrunMarkasi), UrunAdedi, UPPER(UrunOzelligi)
            FROM Urunler
            LIMIT ? OFFSET ?
        """, (items_per_page, offset))

    urunler = cursor.fetchall()

    # Toplam ürün sayısını al
    cursor.execute("SELECT COUNT(*) FROM Urunler")
    total_items = cursor.fetchone()[0]

    # Toplam sayfa sayısını hesapla
    total_pages = (total_items // items_per_page) + (1 if total_items % items_per_page else 0)

    return render_template("anasayfa.html", urunler=urunler, title="Anasayfa", page=page, total_pages=total_pages)

@app.route("/cikis")
def cikis():
    session.pop('username', None) 
    flash("Başarıyla çıkış yapıldı.", "success")
    return redirect("/")

@app.route("/urunekle", methods=["GET", "POST"])
def urunekle():
    if request.method == "POST":
        urun_adi = request.form["urun_adi"]
        urun_markasi = request.form["urun_markasi"]
        urun_adedi = request.form["urun_adedi"]
        urun_ozelligi = request.form["urun_ozelligi"]

        if not urun_adi or not urun_markasi or not urun_adedi or not urun_ozelligi:
            flash("Lütfen tüm alanları doldurunuz!", "error")
            return redirect("/urunekle")

        try:
            connection = create_connection()
            cursor = connection.cursor()

            cursor.execute("""
                        SELECT COUNT(*) FROM Urunler
                           WHERE UrunAdi = ? AND UrunMarkasi = ?
                           """,(urun_adi,urun_markasi))
            urun_var_mi=cursor.fetchone()[0]

            if urun_var_mi > 0:
                flash("Bu ürün zaten var!","error")
                connection.close()
                return redirect("/urunekle")
            
            cursor.execute("""
                INSERT INTO Urunler (UrunAdi, UrunMarkasi, UrunAdedi, UrunOzelligi)
                VALUES (?, ?, ?, ?)
            """, (urun_adi, urun_markasi, urun_adedi, urun_ozelligi))
            connection.commit()
            connection.close()
            flash("Ürün başarıyla eklendi.", "success")
            return redirect("/urunekle")
        except sqlite3.Error as e:
            flash(f"Bir hata oluştu: {e}", "error")
            return redirect("/urunekle")
    else:  # GET
        return render_template("urunekle.html", title="Ürün Ekle")

@app.route("/kullaniciekle", methods=["GET", "POST"])
def kullaniciekle():
    if request.method == "POST":
        ad = request.form.get("ad")
        soyad = request.form.get("soyad")
        kullaniciAdi = request.form.get("kullaniciAdi")
        sifre = request.form.get("sifre")
        sifreTekrar = request.form.get("sifretekrar")

        # Eksik alan kontrolü
        if not ad or not soyad or not kullaniciAdi or not sifre:
            flash("Lütfen tüm alanları doldurunuz!", "error")
            return redirect("/kullaniciekle")

        # Şifre doğrulama
        if sifre != sifreTekrar:
            flash("Şifreler uyuşmuyor! Kullanıcı eklenmedi.", "error")
            return redirect("/kullaniciekle")

        try:
            # Veritabanı bağlantısı ve veri ekleme
            connection = create_connection()
            cursor = connection.cursor()


            cursor.execute("""
                        SELECT COUNT(*) FROM User 
                           WHERE username = ?
                           """,(kullaniciAdi,))
            kullanici_var_mi=cursor.fetchone()[0]
            if kullanici_var_mi > 0:
                flash("Bu kullanıcı adı zaten alınmış!","error")
                connection.close()
                return redirect("/kullaniciekle")

            from werkzeug.security import generate_password_hash

            sifre_hash = generate_password_hash(sifre)  # Şifreyi hash'le
            cursor.execute("""
            INSERT INTO User (name, surname, username, password)
            VALUES (?, ?, ?, ?)
            """, (ad, soyad, kullaniciAdi, sifre_hash))

            connection.commit()
            connection.close()

            flash("Kullanıcı başarıyla eklendi.", "success")
            return redirect("/kullaniciekle")
        except sqlite3.Error as e:
            flash(f"Bir hata oluştu: {e}", "error")
            return redirect("/kullaniciekle")
    else:  # GET metodu için
        return render_template("kullaniciekle.html", title="Kullanıcı Ekle")


@app.route("/profil", methods=["GET", "POST"])
def profil():
    if 'username' not in session:
        flash("Lütfen giriş yapın.", "error")
        return redirect("/girisyap")
    
    username = session['username']
    
    # Veritabanından kullanıcı bilgilerini al
    with create_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(""" 
            SELECT name, surname, username, password FROM User WHERE username = ? 
        """, (username,))
        user_data = cursor.fetchone()
    
    # Eğer kullanıcı bulunamazsa, hata mesajı ver
    if not user_data:
        flash("Kullanıcı bilgileri bulunamadı.", "error")
        return redirect("/cikis")
    
    if request.method == "POST":
        # Formdan gelen veriler
        ad = request.form["ad"]
        soyad = request.form["soyad"]
        kullaniciAdi = request.form["kullaniciAdi"]
        sifre = request.form["sifre"]
        sifreTekrar = request.form["sifretekrar"]

        # Şifre kontrolü
        if sifre != sifreTekrar:
            flash("Şifreler uyuşmuyor!", "error")
            return redirect("/profil")

        # Yeni kullanıcı adı kontrolü
        with create_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(""" 
                UPDATE User SET name = ?, surname = ?, password = ?, username = ? WHERE username = ? 
            """, (ad, soyad, sifre, kullaniciAdi, username))
            connection.commit()
            session['username'] = kullaniciAdi  # Kullanıcı adını güncelledikten sonra session'daki kullanıcı adını da değiştir
            flash("Bilgiler başarıyla güncellendi.", "success")
            return redirect("/profil")  # Başarı mesajı görüntülensin diye aynı sayfaya yönlendiriyoruz
    return render_template("profil.html", user_data=user_data, title="Profil")

@app.route("/urunsil/<int:urun_id>", methods=["POST"])
def urunsil(urun_id):
    try:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("""
            DELETE FROM Urunler WHERE UrunID = ?
        """, (urun_id,))
        connection.commit()
        connection.close()
        flash("Ürün başarıyla silindi.", "success")
    except sqlite3.Error as e:
        flash(f"Bir hata oluştu: {e}", "error")
    return redirect("/anasayfa")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000, debug=True)