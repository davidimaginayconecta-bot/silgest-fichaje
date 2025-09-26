import sys
from datetime import datetime
from PyQt5 import QtCore, QtGui, QtWidgets
from firebase_admin import auth, firestore
from firebase_config import initialize_firebase

# Colores corporativos Silgest
COLOR_PRIMARIO = "#0A3761"
COLOR_SECUNDARIO = "#27AE60"
COLOR_ALERTA = "#E74C3C"
COLOR_FONDO = "#F0F3F8"


class LoginWindow(QtWidgets.QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.user = None
        self.setWindowTitle("Silgest Fichaje - Inicio de sesión")
        self.setGeometry(200, 200, 400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
        # Título en lugar de logo
        title = QtWidgets.QLabel("GRUPO SILGEST")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet(f"color: {COLOR_PRIMARIO}; font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        # Inputs
        self.email_input = QtWidgets.QLineEdit(self)
        self.email_input.setPlaceholderText("Correo electrónico")
        layout.addWidget(self.email_input)
        self.password_input = QtWidgets.QLineEdit(self)
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addWidget(self.password_input)

        login_button = QtWidgets.QPushButton("Iniciar sesión", self)
        login_button.clicked.connect(self.handle_login)
        login_button.setStyleSheet(f"background-color: {COLOR_PRIMARIO}; color: white;")
        layout.addWidget(login_button)
        self.error_label = QtWidgets.QLabel(self)
        self.error_label.setStyleSheet(f"color: {COLOR_ALERTA};")
        layout.addWidget(self.error_label)
        self.setLayout(layout)

    def handle_login(self):
        email = self.email_input.text()
        password = self.password_input.text()
        try:
            user = auth.get_user_by_email(email)
            self.user = user
            self.error_label.setText("")
            self.open_main_window()
        except Exception:
            self.error_label.setText("Error de autenticación. Verifique credenciales.")

    def open_main_window(self):
        self.main_window = MainWindow(self.db, self.user)
        self.main_window.show()
        self.close()


class MainWindow(QtWidgets.QWidget):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.current_entry_id = None
        self.setWindowTitle("Silgest Fichaje")
        self.setGeometry(200, 200, 500, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
        welcome = QtWidgets.QLabel(f"Bienvenido/a, {self.user.display_name or self.user.email}")
        welcome.setAlignment(QtCore.Qt.AlignCenter)
        welcome.setStyleSheet(f"color: {COLOR_PRIMARIO}; font-size: 18px;")
        layout.addWidget(welcome)

        btn_start = QtWidgets.QPushButton("Comenzar jornada", self)
        btn_start.setStyleSheet(f"background-color: {COLOR_SECUNDARIO}; color: white;")
        btn_start.clicked.connect(self.start_work)
        layout.addWidget(btn_start)

        btn_pause = QtWidgets.QPushButton("Pausa / Reanudar", self)
        btn_pause.setStyleSheet(f"background-color: {COLOR_PRIMARIO}; color: white;")
        btn_pause.clicked.connect(self.pause_resume)
        layout.addWidget(btn_pause)

        btn_end = QtWidgets.QPushButton("Finalizar jornada", self)
        btn_end.setStyleSheet(f"background-color: {COLOR_ALERTA}; color: white;")
        btn_end.clicked.connect(self.end_work)
        layout.addWidget(btn_end)

        btn_leave = QtWidgets.QPushButton("Solicitar ausencia", self)
        btn_leave.setStyleSheet(f"background-color: {COLOR_PRIMARIO}; color: white;")
        btn_leave.clicked.connect(self.request_leave)
        layout.addWidget(btn_leave)

        btn_history = QtWidgets.QPushButton("Historial", self)
        btn_history.clicked.connect(self.show_history)
        layout.addWidget(btn_history)

        self.status_label = QtWidgets.QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def start_work(self):
        if self.current_entry_id:
            self.status_label.setText("Ya has iniciado tu jornada.")
            return
        now = datetime.utcnow()
        entry = {
            "uid": self.user.uid,
            "date": now.date().isoformat(),
            "start_at": now.isoformat(),
            "pauses": [],
            "end_at": None,
            "total_ms": 0
        }
        doc_ref = self.db.collection("time_entries").add(entry)
        self.current_entry_id = doc_ref[1].id
        self.status_label.setText("Jornada iniciada.")

    def pause_resume(self):
        if not self.current_entry_id:
            self.status_label.setText("No hay jornada activa.")
            return
        entry_ref = self.db.collection("time_entries").document(self.current_entry_id)
        entry = entry_ref.get().to_dict()
        pauses = entry.get("pauses", [])
        now = datetime.utcnow().isoformat()
        if pauses and pauses[-1].get("pause_end") is None:
            pauses[-1]["pause_end"] = now
            self.status_label.setText("Pausa finalizada.")
        else:
            pauses.append({"pause_start": now, "pause_end": None})
            self.status_label.setText("Pausa iniciada.")
        entry_ref.update({"pauses": pauses})

    def end_work(self):
        if not self.current_entry_id:
            self.status_label.setText("No hay jornada activa.")
            return
        entry_ref = self.db.collection("time_entries").document(self.current_entry_id)
        entry = entry_ref.get().to_dict()
        now = datetime.utcnow()
        start_time = datetime.fromisoformat(entry["start_at"])
        total_ms = int((now - start_time).total_seconds() * 1000)
        for pause in entry["pauses"]:
            if pause.get("pause_end"):
                ps = datetime.fromisoformat(pause["pause_start"])
                pe = datetime.fromisoformat(pause["pause_end"])
                total_ms -= int((pe - ps).total_seconds() * 1000)
        entry_ref.update({
            "end_at": now.isoformat(),
            "total_ms": total_ms
        })
        self.current_entry_id = None
        self.status_label.setText("Jornada finalizada.")

    def request_leave(self):
        self.leave_window = LeaveRequestWindow(self.db, self.user)
        self.leave_window.show()

    def show_history(self):
        self.history_window = HistoryWindow(self.db, self.user)
        self.history_window.show()


class LeaveRequestWindow(QtWidgets.QWidget):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.setWindowTitle("Solicitar ausencia")
        self.setGeometry(250, 250, 400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QFormLayout()
        self.type_combo = QtWidgets.QComboBox(self)
        self.type_combo.addItems(["Vacaciones", "Baja", "Asuntos propios"])
        layout.addRow("Tipo:", self.type_combo)
           # Modalidad: día completo o por horas
        self.kind_combo = QtWidgets.QComboBox(self)
        self.kind_combo.addItems(["Día completo", "Por horas"])
        layout.addRow("Modalidad:", self.kind_combo)
        # Controles día completo
        self.start_date = QtWidgets.QDateEdit(QtCore.QDate.currentDate(), self)
        self.start_date.setCalendarPopup(True)
        self.end_date = QtWidgets.QDateEdit(QtCore.QDate.currentDate(), self)
        self.end_date.setCalendarPopup(True)
        layout.addRow("Desde:", self.start_date)
        layout.addRow("Hasta:", self.end_date)
        # Controles por horas
        self.partial_date = QtWidgets.QDateEdit(QtCore.QDate.currentDate(), self)
        self.partial_date.setCalendarPopup(True)
        self.start_time = QtWidgets.QTimeEdit(QtCore.QTime.currentTime(), self)
        self.end_time = QtWidgets.QTimeEdit(QtCore.QTime.currentTime(), self)
        layout.addRow("Fecha:", self.partial_date)
        layout.addRow("Inicio:", self.start_time)
        layout.addRow("Fin:", self.end_time)
        # Motivo
        self.notes = QtWidgets.QTextEdit(self)
        layout.addRow("Motivo:", self.notes)
        # Botón enviar
        submit_btn = QtWidgets.QPushButton("Enviar solicitud", self)
        submit_btn.setStyleSheet(f"background-color: {COLOR_SECUNDARIO}; color: white;")
        submit_btn.clicked.connect(self.submit_request)
        layout.addRow(submit_btn)
        # Funcón para alternar controles
        def toggle_kind():
            is_partial = (self.kind_combo.currentText() == "Por horas")
            self.start_date.setVisible(not is_partial)
            self.end_date.setVisible(not is_partial)
            self.partial_date.setVisible(is_partial)
            self.start_time.setVisible(is_partial)
            self.end_time.setVisible(is_partial)
        self.kind_combo.currentIndexChanged.connect(lambda _: toggle_kind())
        toggle_kind()
        self.setLayout(layout)

    def submit_request(self):
        kind = "partial_hours" if self.kind_combo.currentText() == "Por horas" else "full_day"
        now_iso = datetime.utcnow().isoformat()
        req = {
            "uid": self.user.uid,
            "type": self.type_combo.currentText(),
            "status": "pending",
            "notes": self.notes.toPlainText(),
            "created_at": now_iso,
            "kind": kind,
        }
        if kind == "full_day":
            from_date = self.start_date.date().toPyDate().isoformat()
            to_date = self.end_date.date().toPyDate().isoformat()
            req["from"] = from_date
            req["to"] = to_date
        else:
            date_str = self.partial_date.date().toPyDate().isoformat()
            start_time = self.start_time.time().toString("HH:mm")
            end_time = self.end_time.time().toString("HH:mm")
            from datetime import datetime as dt
            m1 = dt.strptime(start_time, "%H:%M")
            m2 = dt.strptime(end_time, "%H:%M")
            duration = int((m2 - m1).total_seconds() // 60)
            if duration <= 0:
                QtWidgets.QMessageBox.warning(self, "Hora inválida", "La hora fin debe ser posterior a la de inicio.")
                return
            req.update({
                "date": date_str,
                "start_time": start_time,
                "end_time": end_time,
                "duration_minutes": duration,
            })
        self.db.collection("leave_requests").add(req)
        QtWidgets.QMessageBox.information(self, "Solicitud enviada", "Tu solicitud ha sido enviada correctamente.")
     self.close()  
262
263
264
265
266
267
268
269
270
271
272
273
274
275
276
277
278
279
280
281
282
283
284
285
286
287
288
on("leave_requests").add(req)
        QtWidgets.QMessageBox.information(self, "Solicitud enviada", "Tu solicitud ha sido enviada correctamente.")
        self.close()


class HistoryWindow(QtWidgets.QWidget):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.setWindowTitle("Historial")
        self.setGeometry(260, 260, 500, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
        tabs = QtWidgets.QTabWidget(self)

        tab_fichajes = QtWidgets.QWidget()
        fichaje_layout = QtWidgets.QVBoxLayout()
        fichajes = self.db.collection("time_entries").where("uid", "==", self.user.uid).stream()
        for f in fichajes:
            entry = f.to_dict()
            text = f"{entry['date']}: {entry.get('start_at', '–')} – {entry.get('end_at', '–')} → {entry.get('total_ms', 0)//3600000}h"
            fichaje_layout.addWidget(QtWidgets.QLabel(text))
        tab_fichajes.setLayout(fichaje_layout)
        tabs.addTab(tab_fichajes, "Fichajes")

        tab_ausencias = QtWidgets.QWidget()
        aus_layout = QtWidgets.QVBoxLayout()
        ausencias = self.db.collection("leave_requests").where("uid", "==", self.user.uid).stream()
        for a in ausencias:
            r = a.to_dict()
            text = f"{r['from']} → {r['to']} ({r['type']}) – {r['status']}"
            aus_layout.addWidget(QtWidgets.QLabel(text))
        tab_ausencias.setLayout(aus_layout)
        tabs.addTab(tab_ausencias, "Ausencias")

        layout.addWidget(tabs)
        self.setLayout(layout)


def main():
    initialize_firebase()
    db = firestore.client()
    app = QtWidgets.QApplication(sys.argv)
    login = LoginWindow(db)
    login.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
