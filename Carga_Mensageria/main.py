"""
Carga Mensageria - Main Application (Tkinter GUI)
Replaces Etapas_Carga.frm form layout and event wiring from VB6.

Uses PostgreSQL as the database backend.

Usage:
    python main.py
"""

import threading
import tkinter as tk
from tkinter import messagebox

from db_connection import DatabaseManager
from etapas import EtapaExecutor
from config import DB_CONFIG


class CargaMensageriaApp:
    """Main application window replicating the VB6 Etapas_Carga form."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Etapas da Carga de Mensageria - PostgreSQL")
        self.root.geometry("560x480")
        self.root.resizable(False, False)

        self.executor = EtapaExecutor()
        self._build_gui()

    # ------------------------------------------------------------------
    # GUI Construction
    # ------------------------------------------------------------------
    def _build_gui(self):
        # --- Frame "Banco de Dados" (left side) ---
        db_frame = tk.LabelFrame(self.root, text="Banco de Dados (PostgreSQL)", padx=8, pady=8)
        db_frame.place(x=10, y=10, width=535, height=60)

        conn_str = f"{DB_CONFIG['user']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        tk.Label(db_frame, text="Conexão:").pack(side="left")
        tk.Label(db_frame, text=conn_str, fg="navy", font=("Courier", 9)).pack(
            side="left", padx=4
        )

        # --- Frame "Parametros de Seleção" (below DB frame) ---
        params_frame = tk.LabelFrame(
            self.root, text="Parâmetros de Seleção", padx=8, pady=8
        )
        params_frame.place(x=10, y=75, width=535, height=55)

        tk.Label(params_frame, text="Código Msg:").pack(side="left")
        self.codmsg_var = tk.StringVar(value="GEN0001")
        tk.Entry(params_frame, textvariable=self.codmsg_var, width=12).pack(
            side="left", padx=8
        )

        # --- Step Buttons ---
        btn_x = 10
        btn_w = 535
        btn_h = 28
        gap = 33

        buttons_data = [
            ("Etapa 0a - Atualiza PLAN_Grade", self._run_etapa_0a),
            ("Etapa 0 - Atualiza PLAN_Grade_X_Msg", self._run_etapa_0),
            ("Etapa 1 - Geração da Tabela SPB_CODGRADE", self._run_etapa_1),
            ("Etapa 2 - Geração da Tabela APP_CODGRADE_X_MSG", self._run_etapa_2),
            ("Etapa 3 - Geração da Tabela SPB_MENSAGEM", self._run_etapa_3),
            ("Etapa 4 - Geração do Dicionário de Dados", self._run_etapa_4),
            ("Etapa 5 - Geração da Tabela SPB_MSGFIELD", self._run_etapa_5),
        ]

        self.step_buttons = []
        y = 140
        for text, command in buttons_data:
            btn = tk.Button(self.root, text=text, command=command)
            btn.place(x=btn_x, y=y, width=btn_w, height=btn_h)
            self.step_buttons.append(btn)
            y += gap

        # --- Generation Buttons ---
        y += 8
        gen_buttons = [
            ("Etapa A - Geração de Mensagens no Formato XML", self._run_etapa_a),
            ("Etapa B - Geração de HTML dos Domínios", self._run_etapa_b),
            ("Etapa C - Geração de HTML do ISPB", self._run_etapa_c),
        ]

        for text, command in gen_buttons:
            btn = tk.Button(self.root, text=text, command=command)
            btn.place(x=btn_x, y=y, width=btn_w, height=btn_h)
            self.step_buttons.append(btn)
            y += gap

        # --- Sair (Exit) Button ---
        tk.Button(self.root, text="Sair", command=self.root.quit).place(
            x=480, y=440, width=65, height=25
        )

        # --- Status Bar ---
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor="w",
            padx=5,
        )
        status_bar.place(x=0, y=458, relwidth=1, height=22)

    # ------------------------------------------------------------------
    # Database helper
    # ------------------------------------------------------------------
    def _create_db_manager(self) -> DatabaseManager:
        return DatabaseManager()

    # ------------------------------------------------------------------
    # Generic runner: executes an etapa in a background thread
    # ------------------------------------------------------------------
    def _run_in_thread(self, etapa_func, btn: tk.Button, *args):
        btn.config(state="disabled")
        self.status_var.set(f"Executando {btn.cget('text')}...")
        self.root.config(cursor="wait")
        self.root.update_idletasks()

        def worker():
            try:
                db = self._create_db_manager()
                result = etapa_func(db, *args)
                self.root.after(0, lambda: self._on_success(btn, result))
            except Exception as e:
                err_msg = str(e)
                self.root.after(0, lambda: self._on_error(btn, err_msg))

        threading.Thread(target=worker, daemon=True).start()

    def _on_success(self, btn, message):
        btn.config(state="normal")
        self.root.config(cursor="")
        self.status_var.set(message)
        messagebox.showinfo("Concluído", message)

    def _on_error(self, btn, error_msg):
        btn.config(state="normal")
        self.root.config(cursor="")
        self.status_var.set(f"Erro: {error_msg}")
        messagebox.showerror("Erro", error_msg)

    # ------------------------------------------------------------------
    # Button callbacks
    # ------------------------------------------------------------------
    def _run_etapa_0a(self):
        self._run_in_thread(self.executor.etapa_0a, self.step_buttons[0])

    def _run_etapa_0(self):
        self._run_in_thread(self.executor.etapa_0, self.step_buttons[1])

    def _run_etapa_1(self):
        self._run_in_thread(self.executor.etapa_1, self.step_buttons[2])

    def _run_etapa_2(self):
        self._run_in_thread(self.executor.etapa_2, self.step_buttons[3])

    def _run_etapa_3(self):
        self._run_in_thread(self.executor.etapa_3, self.step_buttons[4])

    def _run_etapa_4(self):
        self._run_in_thread(self.executor.etapa_4, self.step_buttons[5])

    def _run_etapa_5(self):
        self._run_in_thread(self.executor.etapa_5, self.step_buttons[6])

    def _run_etapa_a(self):
        cod_msg = self.codmsg_var.get().strip()
        self._run_in_thread(
            lambda db: self.executor.etapa_a(db, select_cod_msg=cod_msg),
            self.step_buttons[7],
        )

    def _run_etapa_b(self):
        self._run_in_thread(self.executor.etapa_b, self.step_buttons[8])

    def _run_etapa_c(self):
        self._run_in_thread(self.executor.etapa_c, self.step_buttons[9])


def main():
    root = tk.Tk()
    CargaMensageriaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
