from flask import Flask, render_template, request, redirect
import pymysql

app = Flask(__name__, template_folder="./")

# Головна сторінка
@app.route('/')
def index():
    # Отримання списку студентів з бази даних

    return render_template('index.html')

@app.route('/students')
def students():
    # устанавливаем соединение с базой данных
    conn = pymysql.connect(host='localhost', user='root', password='', db='university')
    # Запрос к базе данных на получение данных о студентах, группах и оценках
    query = '''
       SELECT `groups`.name as group_name, students.name as student_name, subjects.name as subject_name, grades.grade
       FROM grades
       JOIN students ON grades.student_id = students.id
       JOIN `groups` ON students.group_id = groups.id
       JOIN subjects ON grades.subject_id = subjects.id
       ORDER BY group_name, student_name, subject_name
       '''
    cursor = conn.cursor()
    cursor.execute(query)
    # Получение всех строк из результата запроса
    rows = cursor.fetchall()

    # Обработка результатов запроса и создание словаря групп
    groups = {}
    current_group = None
    for row in rows:
        group_name = row[0]
        student_name = row[1]
        subject_name = row[2]
        grade = row[3]

        if current_group != group_name:
            current_group = group_name
            groups[group_name] = {'students': []}

        if not any(student['name'] == student_name for student in groups[group_name]['students']):
            groups[group_name]['students'].append({'name': student_name, 'grades': {}})

        for student in groups[group_name]['students']:
            if student['name'] == student_name:
                student['grades'][subject_name] = grade
                break

    return render_template('students.html', groups=groups)

@app.route('/teachers')
def teachers():
    # устанавливаем соединение с базой данных
    conn = pymysql.connect(host='localhost', user='root', password='', db='university')
    # Запрос к базе данных на получение данных о учителях и их предметах
    query = '''
       SELECT teachers.name as teacher_name, subjects.name as subject_name
       FROM `subjects` 
       INNER JOIN `teachers` ON `subjects`.teacher_id = teachers.id 
       ORDER BY teacher_name, subject_name
       '''
    cursor = conn.cursor()
    cursor.execute(query)
    # Получение всех строк из результата запроса
    rows = cursor.fetchall()

    # Обработка результатов запроса и создание словаря учителей
    teachers = {}
    current_teacher = None
    for row in rows:
        teacher_name = row[0]
        subject_name = row[1]

        if current_teacher != teacher_name:
            current_teacher = teacher_name
            teachers[teacher_name] = []

        teachers[teacher_name].append(subject_name)

    return render_template('teachers.html', teachers=teachers)

@app.route('/ranking_for_group')
def ranking_for_group():
    # устанавливаем соединение с базой данных
    conn = pymysql.connect(host='localhost', user='root', password='', db='university')
    # Запрос к базе данных на получение данных о студентах, группах и оценках
    query = '''
        SELECT `groups`.name as group_name, students.id as student_id, students.name as student_name, 
               subjects.name as subject_name, grades.grade
        FROM grades
        JOIN students ON grades.student_id = students.id
        JOIN `groups` ON students.group_id = groups.id
        JOIN subjects ON grades.subject_id = subjects.id
        ORDER BY group_name, student_name, subject_name
    '''
    cursor = conn.cursor()
    cursor.execute(query)

    # Получение всех строк из результата запроса
    rows = cursor.fetchall()

    # Обработка результатов запроса и создание словаря групп
    groups = {}
    current_group = None
    for row in rows:
        group_name = row[0]
        student_id = row[1]
        student_name = row[2]
        subject_name = row[3]
        grade = row[4]

        if current_group != group_name:
            current_group = group_name
            groups[group_name] = {'students': []}

        if not any(student['id'] == student_id for student in groups[group_name]['students']):
            groups[group_name]['students'].append({'id': student_id, 'name': student_name, 'grades': {}})

        for student in groups[group_name]['students']:
            if student['id'] == student_id:
                student['grades'][subject_name] = grade
                break

    # Добавление рейтингового балла для каждого студента
    for group in groups.values():
        for student in group['students']:
            grades_sum = sum(student['grades'].values())
            num_subjects = len(student['grades'])
            student['rating'] = round(grades_sum / num_subjects, 2)


    # Запись рейтинговых баллов в таблицу rankings
    with conn.cursor() as cursor:
        for group in groups.values():
            for student in group['students']:
                query = f"INSERT INTO rankings (student_id, `rank`) VALUES ({student['id']}, {student['rating']})"
                cursor.execute(query)
        conn.commit()

    # Сортировка студентов в каждой группе по рейтингу
    for group in groups.values():
        group['students'] = sorted(group['students'], key=lambda x: x['rating'], reverse=True)

    return render_template('ranking_for_group.html', groups=groups)


@app.route('/ranking')
def ranking():
    # устанавливаем соединение с базой данных
    conn = pymysql.connect(host='localhost', user='root', password='', db='university')
    # Запрос к базе данных на получение данных о студентах, группах и оценках
    query = '''
        SELECT `groups`.name as group_name, students.id as student_id, students.name as student_name, 
               subjects.name as subject_name, grades.grade
        FROM grades
        JOIN students ON grades.student_id = students.id
        JOIN `groups` ON students.group_id = groups.id
        JOIN subjects ON grades.subject_id = subjects.id
        ORDER BY student_name, subject_name
    '''
    cursor = conn.cursor()
    cursor.execute(query)

    # Получение всех строк из результата запроса
    rows = cursor.fetchall()

    # Создание словаря студентов
    students = {}
    for row in rows:
        student_id = row[1]
        student_name = row[2]
        subject_name = row[3]
        grade = row[4]

        if student_id not in students:
            students[student_id] = {'name': student_name, 'group': row[0], 'grades': {}}

        students[student_id]['grades'][subject_name] = grade

    # Добавление рейтингового балла для каждого студента
    for student in students.values():
        grades_sum = sum(student['grades'].values())
        num_subjects = len(student['grades'])
        student['rating'] = round(grades_sum / num_subjects, 2)

    # Запись рейтинговых баллов в таблицу rankings
    with conn.cursor() as cursor:
        for student in students.values():
            query = f"INSERT INTO rankings (student_id, `rank`) VALUES ({student_id}, {student['rating']})"
            cursor.execute(query)
        conn.commit()

    # Сортировка студентов по рейтингу
    students_sorted = sorted(students.values(), key=lambda x: x['rating'], reverse=True)

    return render_template('ranking.html', students_sorted=students_sorted)

@app.route('/students/add')
def add_student():
    conn = pymysql.connect(host='localhost', user='root', password='', db='university')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM `groups`')
    groups = cursor.fetchall()
    print(groups) # добавьте эту строку для отладки
    cursor.execute('SELECT id, name FROM subjects')
    subjects = cursor.fetchall()
    print(subjects) # добавьте эту строку для отладки
    cursor.close()

    return render_template('add_student.html', groups=groups, subjects=subjects)



@app.route('/students/add_form', methods=['GET', 'POST'])
def add_student_form():
    if request.method == 'POST':
        name = request.form['name']
        group_id = request.form['group']
        grades = request.form.getlist('grades[]')
        subject_ids = request.form.getlist('subject_ids[]')

        conn = pymysql.connect(host='localhost', user='root', password='', db='university')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO students (name, group_id) VALUES (%s, %s)', (name, group_id))
        student_id = cursor.lastrowid

        for grade, subject_id in zip(grades, subject_ids):
            cursor.execute('INSERT INTO grades (student_id, subject_id, grade) VALUES (%s, %s, %s)', (student_id, subject_id, grade))

        conn.commit()
        cursor.close()

    return redirect('student.html')

if __name__ == '__main__':
    app.run(debug=True)
