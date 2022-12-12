import os
import sqlite3

# poistaa tietokannan alussa (kätevä moduulin testailussa)
os.remove("courses.db")


db = sqlite3.connect("courses.db")
db.isolation_level = None

# luo tietokantaan tarvittavat taulut
def create_tables():
    
    #taulukko kaikille, opettajat 1, opiskelijat 0
    db.execute("CREATE TABLE Henkilot (id INTEGER PRIMARY KEY, nimi TEXT, if_staff INTEGER, CHECK (0 <= if_staff >=1))")
    db.execute("CREATE TABLE Kurssit (id INTEGER PRIMARY KEY, nimi TEXT, op INTEGER)")
    db.execute("CREATE TABLE KurssinOpettajat (kurssi_id INTEGER REFERENCES Kurssit, opettaja_id INTEGER REFERENCES Henkilot)")
    db.execute("""CREATE TABLE Suoritukset (id INTEGER PRIMARY KEY, kurssi_id INTEGER REFERENCES
               Kurssit, op_id INTEGER REFERENCES Henkilot, pvm DATETIME, arvosana INTEGER)""")
    db.execute("CREATE TABLE Ryhmat (id INTEGER PRIMARY KEY, nimi TEXT)")
    db.execute("CREATE TABLE RyhmanJasenet (ryhma_id INTEGER REFERENCES Ryhmat, henkilo_id INTEGER REFERENCES Henkilot)")



# lisää opettajan tietokantaan
def create_teacher(name):
    
    db.execute("""INSERT INTO Henkilot (nimi, if_staff) VALUES (?, 1)", [name])
    id = db.execute("SELECT id FROM Henkilot WHERE nimi=?""", [name]).fetchone()
    return id[0]

# lisää kurssin tietokantaan
def create_course(name, credits, teacher_ids):
    
    db.execute("INSERT INTO Kurssit (nimi, op) VALUES (?, ?)", [name, credits])
    k_id = db.execute("SELECT id FROM Kurssit WHERE nimi=?", [name]).fetchone()
    if len(teacher_ids) != 0:
        for i in teacher_ids:
            db.execute("INSERT INTO KurssinOpettajat (kurssi_id, opettaja_id) VALUES (?, ?)", [k_id[0], i])
    if len(teacher_ids) == 0:
        db.execute("INSERT INTO KurssinOpettajat (kurssi_id, opettaja_id) VALUES (?, NULL)", [k_id[0]])
    return k_id[0]

# lisää opiskelijan tietokantaan
def create_student(name):
    
    db.execute("INSERT INTO Henkilot (nimi, if_staff) VALUES (?, 0)", [name])
    id = db.execute("SELECT id FROM Henkilot WHERE nimi=?", [name]).fetchone()
    return id[0]
    
# antaa opiskelijalle suorituksen kurssista
def add_credits(student_id, course_id, date, grade):
    
    db.execute("INSERT INTO Suoritukset (kurssi_id, op_id, pvm, arvosana) VALUES (?, ?, ?, ?)",
               [course_id, student_id, date, grade])


# lisää ryhmän tietokantaan
def create_group(name, teacher_ids, student_ids):
    
    db.execute("INSERT INTO Ryhmat (nimi) VALUES (?)", [name])
    ryhm_id = db.execute("SELECT id FROM Ryhmat WHERE nimi=?", [name]).fetchone()
    
    ryhm_id = ryhm_id[0]
    
    for i in teacher_ids:
        db.execute("INSERT INTO RyhmanJasenet (ryhma_id, henkilo_id) VALUES (?, ?)", [ryhm_id, i])
    for i in student_ids:
        db.execute("INSERT INTO RyhmanJasenet (ryhma_id, henkilo_id) VALUES (?, ?)", [ryhm_id, i])


# hakee kurssit, joissa opettaja opettaa (aakkosjärjestyksessä)
def courses_by_teacher(teacher_name):
    
    placeholder = db.execute("""SELECT K.nimi FROM Kurssit K, Henkilot H, KurssinOpettajat KO 
                             WHERE KO.kurssi_id=K.id AND KO.opettaja_id=H.id AND H.nimi=?""", 
                             [teacher_name]).fetchall()
    return [i[0] for i in placeholder]

# hakee opettajan antamien opintopisteiden määrän
def credits_by_teacher(teacher_name):
    
    credits = db.execute("""SELECT SUM(K.op) FROM Kurssit K, Henkilot H, KurssinOpettajat KO, Suoritukset S 
                         WHERE S.kurssi_id=K.id AND KO.kurssi_id=K.id AND KO.opettaja_id=H.id AND H.nimi=?""", 
                         [teacher_name]).fetchone()
    return credits[0]

# hakee opiskelijan suorittamat kurssit (aakkosjärjestyksessä)
def courses_by_student(student_name):
    
    return db.execute("""SELECT K.nimi, S.arvosana FROM Kurssit K, Henkilot H, Suoritukset S 
                      WHERE K.id = S.kurssi_id AND S.op_id = H.id and H.nimi=? ORDER BY 1 ASC""", 
                      [student_name]).fetchall()

# hakee tiettynä vuonna saatujen opintopisteiden määrän
def credits_by_year(year):
    
    year = str(year)
    credits = db.execute("""SELECT SUM(K.op) FROM Kurssit K, Suoritukset S 
                         WHERE K.id = S.kurssi_id AND strftime('%Y', S.pvm)= ?""", 
                         [year]).fetchone()
    return credits[0]


# hakee kurssin arvosanojen jakauman
def grade_distribution(course_name):
    
    dict = {}
    for i in range(1, 6):
        result=db.execute("""SELECT COUNT(S.arvosana) FROM Suoritukset S, Kurssit K 
                          WHERE S.arvosana = ? AND S.kurssi_id = K.id AND K.nimi=?""", 
                          [i, course_name]).fetchone()
        dict[i] = result[0]
    return dict

# hakee listan kursseista (nimi, opettajien määrä, suorittajien määrä)
def course_list():
    
    return db.execute("""SELECT K.nimi, COUNT(DISTINCT KO.opettaja_id), COUNT(DISTINCT S.op_id) 
                      FROM KurssinOpettajat KO, Kurssit K LEFT JOIN Suoritukset S ON K.id = S.kurssi_id 
                      WHERE K.id = KO.kurssi_id GROUP BY K.nimi""").fetchall()


# hakee ryhmässä olevat henkilöt (aakkosjärjestyksessä)
def group_people(group_name):
                      
    people = db.execute("""SELECT H.nimi FROM Henkilot H, Ryhmat R, RyhmanJasenet RJ 
                        WHERE R.nimi=? AND R.id = RJ.ryhma_id AND H.id = RJ.henkilo_id ORDER BY 1""", 
                        [group_name]).fetchall()
    return [i[0] for i in people]

# hakee ryhmissä saatujen opintopisteiden määrät (aakkosjärjestyksessä)
def credits_in_groups():
                      
    return db.execute("""SELECT R.nimi, IFNULL(SUM(K.op), 0) FROM Ryhmat R 
                      LEFT JOIN RyhmanJasenet RJ ON R.id = RJ.ryhma_id 
                      LEFT JOIN Henkilot H ON RJ.henkilo_id = H.id 
                      LEFT JOIN Suoritukset S ON H.id =S.op_id 
                      LEFT JOIN Kurssit K ON S.kurssi_id = K.id 
                      GROUP BY R.nimi ORDER BY 1 ASC""").fetchall()

# hakee ryhmät, joissa on tietty opettaja ja opiskelija (aakkosjärjestyksessä)
def common_groups(teacher_name, student_name):
                      
    groups = db.execute("""SELECT R.nimi FROM Ryhmat R, RyhmanJasenet RJ, RyhmanJasenet RK 
                        WHERE R.id = RJ.ryhma_id AND R.id = RK.ryhma_id AND RJ.ryhma_id 
                        IN (SELECT RJ.ryhma_id FROM RyhmanJasenet RJ, Henkilot H WHERE H.nimi=? AND H.id = RJ.henkilo_id) 
                        AND RK.ryhma_id IN (SELECT RK.ryhma_id FROM RyhmanJasenet RK, Henkilot H WHERE H.nimi=? AND H.id = RK.henkilo_id) 
                        GROUP BY R.nimi""", [teacher_name, student_name]).fetchall()
    return [i[0] for i in groups]
