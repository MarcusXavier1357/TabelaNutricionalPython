import json
import os
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

# ==================================================
# BACKEND (Lógica de negócios e dados)
# ==================================================
class Ingrediente:
    """Classe para representar um ingrediente com suas informações nutricionais"""
    def __init__(self, nome, carboidrato_por_g, proteina_por_g, gordura_por_g, fibra_por_g, sodio_por_g):
        self.nome = nome
        self.carboidrato_por_g = carboidrato_por_g
        self.proteina_por_g = proteina_por_g
        self.gordura_por_g = gordura_por_g
        self.fibra_por_g = fibra_por_g
        self.sodio_por_g = sodio_por_g
    
    def to_dict(self):
        """Converte o objeto para dicionário para salvar em JSON"""
        return {
            'nome': self.nome,
            'carboidrato_por_g': self.carboidrato_por_g,
            'proteina_por_g': self.proteina_por_g,
            'gordura_por_g': self.gordura_por_g,
            'fibra_por_g': self.fibra_por_g,
            'sodio_por_g': self.sodio_por_g
        }

class Receita:
    """Classe para representar uma receita com múltiplos ingredientes"""
    def __init__(self, nome, ingredientes, rendimento_total):
        self.nome = nome
        self.ingredientes = ingredientes  # Lista de tuplas (Ingrediente, quantidade em gramas)
        self.rendimento_total = rendimento_total  # Gramas totais da receita final
    
    def to_dict(self):
        return {
            'nome': self.nome,
            'ingredientes': [
                (ingrediente.nome, quantidade) 
                for ingrediente, quantidade in self.ingredientes
            ],
            'rendimento_total': self.rendimento_total
        }

class DataManager:
    """Classe para gerenciar o carregamento e salvamento de dados"""
    INGREDIENTES_FILE = 'ingredientes.json'
    RECEITAS_FILE = 'receitas.json'
    
    @classmethod
    def carregar_ingredientes(cls):
        """Carrega ingredientes do arquivo JSON"""
        if not os.path.exists(cls.INGREDIENTES_FILE):
            return []
        
        with open(cls.INGREDIENTES_FILE, 'r') as f:
            dados = json.load(f)
        
        ingredientes = []
        for item in dados:
            # Usar get() com valor padrão para compatibilidade com versões antigas
            ingredientes.append(
                Ingrediente(
                    nome=item['nome'],
                    carboidrato_por_g=item['carboidrato_por_g'],
                    proteina_por_g=item['proteina_por_g'],
                    gordura_por_g=item['gordura_por_g'],
                    fibra_por_g=item['fibra_por_g'],
                    sodio_por_g=item['sodio_por_g']
                )
            )
        return ingredientes
    
    @classmethod
    def salvar_ingredientes(cls, ingredientes):
        """Salva lista de ingredientes no arquivo JSON"""
        with open(cls.INGREDIENTES_FILE, 'w') as f:
            json.dump([i.to_dict() for i in ingredientes], f, indent=4)
    
    @classmethod
    def carregar_receitas(cls, ingredientes):
        try:
            if not os.path.exists(cls.RECEITAS_FILE):
                return []
            
            with open(cls.RECEITAS_FILE, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                
            receitas = []
            for item in dados:
                ingredientes_receita = []
                for nome_ing, qtd in item['ingredientes']:
                    ingrediente = next((i for i in ingredientes if i.nome == nome_ing), None)
                    if ingrediente:
                        ingredientes_receita.append((ingrediente, qtd))
                
                receitas.append(Receita(
                    item['nome'],
                    ingredientes_receita,
                    item.get('rendimento_total', sum(qtd for _, qtd in ingredientes_receita))
                ))
                
            return receitas
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar receitas: {str(e)}")
            return []
        
    @classmethod
    def salvar_receitas(cls, receitas):
        try:
            dados = [{
                'nome': r.nome,
                'ingredientes': [(ing.nome, qtd) for ing, qtd in r.ingredientes],
                'rendimento_total': r.rendimento_total
            } for r in receitas]
            
            with open(cls.RECEITAS_FILE, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar receitas: {str(e)}")

    @classmethod
    def deletar_ingrediente(cls, nome):
        ingredientes = cls.carregar_ingredientes()
        ingredientes = [i for i in ingredientes if i.nome != nome]
        cls.salvar_ingredientes(ingredientes)
    
    @classmethod
    def deletar_receita(cls, nome):
        receitas = cls.carregar_receitas()
        receitas = [r for r in receitas if r.nome != nome]
        cls.salvar_receitas(receitas)

class CalculadoraNutricional:
    @staticmethod
    def calcular_por_porcao(receitas_porcoes):
        totais = {
            'carboidratos': 0.0,
            'proteina': 0.0,
            'gordura': 0.0,
            'fibra': 0.0,
            'sodio': 0.0,
            'calorias': 0.0
        }
        
        for receita, porcao in receitas_porcoes:
            if receita.rendimento_total <= 0:
                raise ValueError(f"Receita {receita.nome} tem rendimento total inválido")
            
            fator = porcao / receita.rendimento_total  # Fator baseado no rendimento total
            
            for ingrediente, qtd in receita.ingredientes:
                quantidade_efetiva = qtd * fator
                totais['carboidratos'] += quantidade_efetiva * ingrediente.carboidrato_por_g
                totais['proteina'] += quantidade_efetiva * ingrediente.proteina_por_g
                totais['gordura'] += quantidade_efetiva * ingrediente.gordura_por_g
                totais['calorias'] += (quantidade_efetiva * ingrediente.carboidrato_por_g * 4 +
                                      quantidade_efetiva * ingrediente.proteina_por_g * 4 +
                                      quantidade_efetiva * ingrediente.gordura_por_g * 9)
                totais['fibra'] += quantidade_efetiva * ingrediente.fibra_por_g
                totais['sodio'] += quantidade_efetiva * ingrediente.sodio_por_g
                
        return {k: round(v, 2) for k, v in totais.items()}

class ValoresDiarios:
    VD_FILE = 'valores_diarios.json'
    
    @classmethod
    def carregar(cls):
        try:
            with open(cls.VD_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "carboidratos": 300,
                "proteinas": 75,
                "gorduras_totais": 55,
                "valor_energetico": 2000,
                "fibras": 30,
                "sodio": 5000
            }
    
    @classmethod
    def salvar(cls, dados):
        with open(cls.VD_FILE, 'w') as f:
            json.dump(dados, f, indent=4)

class GeradorPDF:
    @staticmethod
    def gerar_tabela_nutricional(nome_arquivo, dados_nutricionais, peso_porcao):
        doc = SimpleDocTemplate(nome_arquivo, pagesize=letter)
        elementos = []
        
        # Carregar valores diários
        vd = ValoresDiarios.carregar()
        
        # Calcular valores energéticos
        kcal = (dados_nutricionais['carboidratos'] * 4) + \
               (dados_nutricionais['proteina'] * 4) + \
               (dados_nutricionais['gordura'] * 9)
        kj = kcal * 4.184

        # Calcular porcentagens
        porcentagens = {
            'carboidratos': (dados_nutricionais['carboidratos'] / vd['carboidratos']) * 100,
            'proteina': (dados_nutricionais['proteina'] / vd['proteinas']) * 100,
            'gordura': (dados_nutricionais['gordura'] / vd['gorduras_totais']) * 100,
            'kcal': (kcal / vd['valor_energetico']) * 100,
            'fibra': (dados_nutricionais['fibra'] / vd['fibras']) * 100,
            'sodio': (dados_nutricionais['sodio'] / vd['sodio']) * 100
        }

        # Estilos
        styles = getSampleStyleSheet()
        estilo_cabecalho = styles["BodyText"]
        estilo_cabecalho.alignment = TA_CENTER
        estilo_rodape = ParagraphStyle(
            name='Italic',
            parent=styles["Italic"],
            fontSize=8,
            leading=10
        )
        
        texto_rodape = (
            "*% Valores Diários de referência com base em uma dieta de {} kcal ou {} kJ. "
            "Seus valores diários podem ser maiores ou menores dependendo de suas necessidades energéticas."
            .format(vd['valor_energetico'], int(vd['valor_energetico'] * 4.184))
        )

        # Dados da tabela
        tabela_dados = [
            [Paragraph("<b>INFORMAÇÃO NUTRICIONAL</b><br/>Marmita de {}g".format(peso_porcao), estilo_cabecalho), '', ''],
            ["", "Quantidade nesta marmita", "%VD*"],
            ["Valor Energético", f"{kcal:.1f} kcal = {kj:.0f} kJ", f"{porcentagens['kcal']:.1f}%"],
            ["Carboidratos", f"{dados_nutricionais['carboidratos']:.1f} g", f"{porcentagens['carboidratos']:.1f}%"],
            ["Proteínas", f"{dados_nutricionais['proteina']:.1f} g", f"{porcentagens['proteina']:.1f}%"],
            ["Gorduras Totais", f"{dados_nutricionais['gordura']:.1f} g", f"{porcentagens['gordura']:.1f}%"],
            ["Fibra Alimentar", f"{dados_nutricionais['fibra']:.1f} g", f"{porcentagens['fibra']:.1f}%"],
            ["Sódio", f"{dados_nutricionais['sodio']:.1f} mg", f"{porcentagens['sodio']:.1f}%"],
            [Paragraph(texto_rodape, estilo_rodape), '', '']
        ]

        # Estilo da tabela
        estilo = TableStyle([
            ('SPAN', (0,0), (-1,0)),  # Mesclar linha do cabeçalho
            ('SPAN', (0,8), (-1,8)), # Mesclar linha do rodapé
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('BACKGROUND', (0,1), (-1,1), colors.beige),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('FONTSIZE', (0,1), (-1,-1), 10),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,8), (-1,8), 'LEFT'),
            ('FONTNAME', (0,8), (-1,8), 'Helvetica'),
            ('TEXTCOLOR', (0,8), (-1,8), colors.dimgray),
        ])

        # Criar e formatar tabela
        tabela = Table(tabela_dados, colWidths=[120, 140, 50])
        tabela.setStyle(estilo)
        elementos.append(tabela)

        doc.build(elementos)

# ==================================================
# FRONTEND (Interface gráfica)
# ==================================================
class NutritionApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema Nutricional - Restaurante")
        self.geometry("800x600")
        
        # Carregar dados
        self.ingredientes = DataManager.carregar_ingredientes() or []
        self.receitas = DataManager.carregar_receitas(self.ingredientes) or []  # Correção aqui
        
        self.ingrediente_selecionado = None
        self.receita_selecionada = None

        # Criar abas
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill='both', expand=True)
        
        # Abas
        self.tab_ingredientes = self.tabview.add("Ingredientes")
        self.tab_receitas = self.tabview.add("Receitas")
        self.tab_gerar = self.tabview.add("Gerar PDF")
        self.tab_config = self.tabview.add("Configurações")
        
        # Widgets das abas
        self._criar_aba_ingredientes()
        self._criar_aba_receitas()
        self._criar_aba_gerar()
        self._criar_aba_config()
    
    def _criar_aba_config(self):
        frame = ctk.CTkFrame(self.tab_config)
        frame.pack(pady=20, padx=20, fill='both', expand=True)

        campos = [
            ("Carboidratos (g):", 'vd_carb'),
            ("Proteínas (g):", 'vd_prot'),
            ("Gorduras Totais (g):", 'vd_gord'),
            ("Fibras Alimentares (g):", 'vd_fibra'),
            ("Sódio (mg):", 'vd_sodio'),
            ("Valor Energético (kcal):", 'vd_kcal')
        ]

        for i, (label, attr) in enumerate(campos):
            ctk.CTkLabel(frame, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='w')
            entry = ctk.CTkEntry(frame)
            entry.grid(row=i, column=1, padx=5, pady=5)
            setattr(self, attr, entry)

        # Carregar valores atuais
        vd = ValoresDiarios.carregar()
        self.vd_carb.insert(0, str(vd['carboidratos']))
        self.vd_prot.insert(0, str(vd['proteinas']))
        self.vd_gord.insert(0, str(vd['gorduras_totais']))
        self.vd_fibra.insert(0, str(vd['fibras']))
        self.vd_sodio.insert(0, str(vd['sodio']))
        self.vd_kcal.insert(0, str(vd['valor_energetico']))

        btn_salvar = ctk.CTkButton(
            frame,
            text="Salvar Valores Diários",
            command=self._salvar_vds
        )
        btn_salvar.grid(row=7, columnspan=2, pady=10)

    def _salvar_vds(self):
        try:
            novos_vd = {
                "carboidratos": float(self.vd_carb.get()),
                "proteinas": float(self.vd_prot.get()),
                "gorduras_totais": float(self.vd_gord.get()),
                "fibras_alimentares": float(self.vd_fibra.get()),
                "sodio": float(self.vd_sodio.get()),
                "valor_energetico": float(self.vd_kcal.get())
            }
            ValoresDiarios.salvar(novos_vd)
            messagebox.showinfo("Sucesso", "Valores atualizados!")
        except ValueError:
            messagebox.showerror("Erro", "Valores inválidos!")

    def _criar_aba_ingredientes(self):
        # Formulário para novo ingrediente
        frame_form = ctk.CTkFrame(self.tab_ingredientes)
        frame_form.pack(pady=10, padx=10, fill='x')

        # Seletor de ingredientes existentes
        frame_selecao = ctk.CTkFrame(frame_form)
        frame_selecao.grid(row=0, column=0, columnspan=2, pady=5, sticky='ew')
        
        self.combo_ingredientes_exist = ctk.CTkComboBox(
            frame_selecao,
            values=[i.nome for i in self.ingredientes],
            command=self._carregar_ingrediente_selecionado
        )
        self.combo_ingredientes_exist.pack(side='left', padx=5, pady=5, fill='x', expand=True)
        
        btn_carregar = ctk.CTkButton(
            frame_selecao,
            text="Carregar",
            command=self._carregar_ingrediente_selecionado
        )
        btn_carregar.pack(side='left', padx=5)
        
        btn_novo = ctk.CTkButton(
            frame_selecao,
            text="Novo",
            command=self._novo_ingrediente
        )
        btn_novo.pack(side='left', padx=5)

        btn_deletar = ctk.CTkButton(
            frame_selecao,
            text="Deletar",
            command=self._deletar_ingrediente,
            fg_color="#d9534f",
            hover_color="#c9302c"
        )
        btn_deletar.pack(side='left', padx=5)
        
        # Campos do formulário
        campos = [
            ("Nome", 'entry_nome'),
            ("Carboidratos por g", 'entry_carb'),
            ("Proteínas por g", 'entry_prot'),
            ("Gorduras por g", 'entry_gord'),
            ("Fibras por g", 'entry_fibra'),
            ("Sódio por mg", 'entry_sodio')
        ]
        
        for i, (label, attr) in enumerate(campos, start=1):
            ctk.CTkLabel(frame_form, text=label).grid(row=i, column=0, padx=5, pady=5)
            entry = ctk.CTkEntry(frame_form)
            entry.grid(row=i, column=1, padx=5, pady=5)
            setattr(self, attr, entry)
        
        # Botões
        btn_salvar = ctk.CTkButton(
            frame_form, 
            text="Salvar Alterações" if self.ingrediente_selecionado else "Salvar Novo",
            command=self.salvar_ingrediente
        )
        btn_salvar.grid(row=7, column=0, columnspan=2, pady=10)

    def _carregar_ingrediente_selecionado(self, event=None):
        nome = self.combo_ingredientes_exist.get()
        if not nome:
            return
        
        ingrediente = next((i for i in self.ingredientes if i.nome == nome), None)
        if not ingrediente:
            return
        
        self.ingrediente_selecionado = ingrediente
        
        # Preencher campos do formulário
        self.entry_nome.delete(0, 'end')
        self.entry_nome.insert(0, ingrediente.nome)
        self.entry_carb.delete(0, 'end')
        self.entry_carb.insert(0, str(ingrediente.carboidrato_por_g))
        self.entry_prot.delete(0, 'end')
        self.entry_prot.insert(0, str(ingrediente.proteina_por_g))
        self.entry_gord.delete(0, 'end')
        self.entry_gord.insert(0, str(ingrediente.gordura_por_g))
        self.entry_fibra.delete(0, 'end')
        self.entry_fibra.insert(0, str(ingrediente.fibra_por_g))
        self.entry_sodio.delete(0, 'end')
        self.entry_sodio.insert(0, str(ingrediente.sodio_por_g))

    def _novo_ingrediente(self):
        self.ingrediente_selecionado = None
        self.combo_ingredientes_exist.set('')
        self.entry_nome.delete(0, 'end')
        self.entry_carb.delete(0, 'end')
        self.entry_prot.delete(0, 'end')
        self.entry_gord.delete(0, 'end')
        self.entry_fibra.delete(0, 'end')
        self.entry_sodio.delete(0, 'end')

    def salvar_ingrediente(self):
        try:
            nome = self.entry_nome.get()
            carb = float(self.entry_carb.get())
            prot = float(self.entry_prot.get())
            gord = float(self.entry_gord.get())
            fibra = float(self.entry_fibra.get() or 0.0)
            sodio = float(self.entry_sodio.get() or 0.0)
        except ValueError:
            messagebox.showerror("Erro", "Preencha todos os campos corretamente")
            return

        if self.ingrediente_selecionado:
            # Modo edição
            ingrediente = self.ingrediente_selecionado
            old_name = ingrediente.nome
            
            # Atualizar dados
            ingrediente.nome = nome
            ingrediente.carboidrato_por_g = carb
            ingrediente.proteina_por_g = prot
            ingrediente.gordura_por_g = gord
            
            # Atualizar combos
            if old_name != nome:
                self._atualizar_combos_ingredientes(old_name, nome)
        else:
            # Modo novo ingrediente
            novo_ing = Ingrediente(nome, carb, prot, gord, fibra, sodio)
            self.ingredientes.append(novo_ing)
            
        DataManager.salvar_ingredientes(self.ingredientes)
        self._atualizar_combos()
        messagebox.showinfo("Sucesso", "Ingrediente salvo com sucesso!")
        self._novo_ingrediente()

    def _atualizar_combos(self):
        # Atualizar lista de ingredientes
        valores = [i.nome for i in self.ingredientes]
        self.combo_ingredientes_exist.configure(values=valores)
        self.combo_ingredientes.configure(values=valores)

    def _atualizar_combos_ingredientes(self, old_name, new_name):
        # Atualizar receitas que usam o ingrediente renomeado
        for receita in self.receitas:
            for i, (ing, qtd) in enumerate(receita.ingredientes):
                if ing.nome == old_name:
                    receita.ingredientes[i] = (self.ingrediente_selecionado, qtd)
        DataManager.salvar_receitas(self.receitas)
    
    def _criar_aba_receitas(self):
        # Frame principal
        frame_form = ctk.CTkFrame(self.tab_receitas)
        frame_form.pack(pady=10, padx=10, fill='both', expand=True)

        # Seletor de receitas
        frame_selecao = ctk.CTkFrame(frame_form)
        frame_selecao.pack(fill='x', pady=5)
        
        self.combo_receitas_exist = ctk.CTkComboBox(
            frame_selecao,
            values=[r.nome for r in self.receitas]
        )
        self.combo_receitas_exist.pack(side='left', padx=5, fill='x', expand=True)
        
        btn_carregar = ctk.CTkButton(
            frame_selecao,
            text="Carregar",
            command=self._carregar_receita_selecionada
        )
        btn_carregar.pack(side='left', padx=5)
        
        btn_nova = ctk.CTkButton(
            frame_selecao,
            text="Nova",
            command=self._nova_receita
        )
        btn_nova.pack(side='left', padx=5)

        btn_deletar = ctk.CTkButton(
            frame_selecao,
            text="Deletar",
            command=self._deletar_receita,
            fg_color="#d9534f",
            hover_color="#c9302c"
        )
        btn_deletar.pack(side='left', padx=5)

        # Campos do formulário
        ctk.CTkLabel(frame_form, text="Nome da Receita:").pack(pady=5)
        self.entry_nome_receita = ctk.CTkEntry(frame_form)
        self.entry_nome_receita.pack(fill='x', pady=5)

        ctk.CTkLabel(frame_form, text="Rendimento Total (g):").pack(pady=5)
        self.entry_rendimento_total = ctk.CTkEntry(frame_form)
        self.entry_rendimento_total.pack(fill='x', pady=5)

        # Frame para ingredientes
        frame_ingredientes = ctk.CTkFrame(frame_form)
        frame_ingredientes.pack(fill='x', pady=5)
        
        self.combo_ingredientes = ctk.CTkComboBox(
            frame_ingredientes,
            values=[i.nome for i in self.ingredientes]
        )
        self.combo_ingredientes.pack(side='left', padx=5, fill='x', expand=True)
        
        self.entry_quantidade = ctk.CTkEntry(frame_ingredientes, width=100)
        self.entry_quantidade.pack(side='left', padx=5)
        
        btn_add = ctk.CTkButton(
            frame_ingredientes,
            text="Adicionar",
            command=self.adicionar_ingrediente_receita
        )
        btn_add.pack(side='left', padx=5)

        # Lista de ingredientes ÚNICA COM PACK()
        self.lista_ingredientes = ctk.CTkTextbox(frame_form, height=150)
        self.lista_ingredientes.pack(fill='both', expand=True, pady=5)

        # Botão salvar
        btn_salvar = ctk.CTkButton(
            frame_form,
            text="Salvar Receita",
            command=self.salvar_receita
        )
        btn_salvar.pack(pady=10)
    
    def _carregar_receita_selecionada(self, event=None):
        nome = self.combo_receitas_exist.get()
        if not nome:
            return
        
        receita = next((r for r in self.receitas if r.nome == nome), None)
        if not receita:
            return
        
        self.receita_selecionada = receita
        
        # Preencher campos do formulário
        self.entry_nome_receita.delete(0, 'end')
        self.entry_nome_receita.insert(0, receita.nome)
        
        # Preencher campo de rendimento total
        self.entry_rendimento_total.delete(0, 'end')
        self.entry_rendimento_total.insert(0, str(receita.rendimento_total))

        # Limpar e preencher ingredientes
        self.lista_ingredientes.delete('1.0', 'end')
        for ing, qtd in receita.ingredientes:
            self.lista_ingredientes.insert('end', f"{ing.nome} - {qtd}g\n")

    def _nova_receita(self):
        self.receita_selecionada = None
        self.combo_receitas_exist.set('')
        self.entry_nome_receita.delete(0, 'end')
        self.lista_ingredientes.delete('1.0', 'end')

    def salvar_receita(self):
        try:
            rendimento_total = float(self.entry_rendimento_total.get())
            if rendimento_total <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Rendimento total deve ser um número positivo")
            return
        
        # Validação básica
        nome = self.entry_nome_receita.get()
        ingredientes_texto = self.lista_ingredientes.get('1.0', 'end').strip()

        if self.receita_selecionada:
            # Modo edição - atualizar dados
            index = self.receitas.index(self.receita_selecionada)
            self.receitas[index] = Receita(nome, ingredientes, rendimento_total)
        else:
            # Modo nova receita
            nova_receita = Receita(
                nome=nome,
                ingredientes=ingredientes,
                rendimento_total=rendimento_total  
            )
            self.receitas.append(nova_receita)
        
        if not nome or not ingredientes_texto:
            messagebox.showerror("Erro", "Preencha todos os campos")
            return
        
        # Processar ingredientes
        ingredientes = []
        for line in ingredientes_texto.split('\n'):
            if not line:
                continue
            try:
                nome_ing, resto = line.split(' - ')
                quantidade = int(resto.replace('g', '').strip())
                ingrediente = next(i for i in self.ingredientes if i.nome == nome_ing)
                ingredientes.append((ingrediente, quantidade))
            except Exception as e:
                messagebox.showerror("Erro", f"Formato inválido na linha: {line}")
                return
        
        if self.receita_selecionada:
            # Modo edição - atualizar receita existente
            old_name = self.receita_selecionada.nome
            self.receita_selecionada.nome = nome
            self.receita_selecionada.ingredientes = ingredientes
            self.receita_selecionada.peso_total = sum(qtd for _, qtd in ingredientes)
            
            if old_name != nome:
                # Atualizar combos
                valores = [r.nome for r in self.receitas]
                self.combo_receitas_exist.configure(values=valores)
        else:
            # Modo nova receita
            if any(r.nome == nome for r in self.receitas):
                messagebox.showerror("Erro", "Já existe uma receita com este nome!")
                return
            
            nova_receita = Receita(nome, ingredientes)
            self.receitas.append(nova_receita)
        
        DataManager.salvar_receitas(self.receitas)
        self._atualizar_combos_receitas()
        messagebox.showinfo("Sucesso", "Receita salva com sucesso!")
        self._nova_receita()

    def _atualizar_combos_receitas(self):
        valores = [r.nome for r in self.receitas]
        self.combo_receitas_exist.configure(values=valores)
        # Atualizar também o combo da aba de gerar PDF
        for frame in self.frame_receitas.winfo_children():
            for child in frame.winfo_children():
                if isinstance(child, ctk.CTkComboBox):
                    current_value = child.get()
                    child.configure(values=valores)
                    child.set(current_value)

    def _criar_aba_gerar(self):
        frame = ctk.CTkFrame(self.tab_gerar)
        frame.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Seleção de receitas
        ctk.CTkLabel(frame, text="Selecione as Receitas e Quantidades:").pack(pady=5)
        
        self.receitas_porcoes = []
        
        # Frame para adicionar receitas
        self.frame_receitas = ctk.CTkScrollableFrame(frame)
        self.frame_receitas.pack(fill='both', expand=True, pady=10)
        
        # Botão para adicionar receita
        btn_add_receita = ctk.CTkButton(
            frame,
            text="Adicionar Receita",
            command=self.adicionar_receita_porcao
        )
        btn_add_receita.pack(pady=5)
        
        # Botão gerar PDF
        btn_gerar = ctk.CTkButton(
            frame,
            text="Gerar PDF",
            command=self.gerar_pdf
        )
        btn_gerar.pack(pady=10)
    
    def adicionar_receita_porcao(self):
        # Cria um novo frame para cada receita/porção
        frame = ctk.CTkFrame(self.frame_receitas)
        frame.pack(fill='x', pady=2)
        
        # Combobox de receitas
        combo = ctk.CTkComboBox(
            frame,
            values=[r.nome for r in self.receitas]
        )
        combo.pack(side='left', padx=5)
        
        # Entrada de quantidade
        entry = ctk.CTkEntry(frame, width=100, placeholder_text="Gramas")
        entry.pack(side='left', padx=5)
        
        # Botão remover
        btn_remove = ctk.CTkButton(
            frame,
            text="X",
            width=30,
            command=lambda f=frame: f.destroy()
        )
        btn_remove.pack(side='right', padx=5)
    
    # ====================
    # Métodos de negócio
    # ====================
    def salvar_ingrediente(self):
        try:
            nome = self.entry_nome.get()
            carb = float(self.entry_carb.get())
            prot = float(self.entry_prot.get())
            gord = float(self.entry_gord.get())
            fibra = float(self.entry_fibra.get())
            sodio = float(self.entry_sodio.get())
        except ValueError:
            messagebox.showerror("Erro", "Preencha todos os campos corretamente")
            return

        if self.ingrediente_selecionado:
            # Modo edição - Alterar ingrediente existente
            ingrediente = self.ingrediente_selecionado
            old_name = ingrediente.nome
            
            # Atualizar dados do objeto existente
            ingrediente.nome = nome
            ingrediente.carboidrato_por_g = carb
            ingrediente.proteina_por_g = prot
            ingrediente.gordura_por_g = gord
            ingrediente.fibra_por_g = fibra
            ingrediente.sodio_por_g = sodio
            
            # Atualizar combos se o nome mudou
            if old_name != nome:
                self._atualizar_combos_ingredientes(old_name, nome)
        else:
            # Modo novo ingrediente
            # Verificar se já existe ingrediente com esse nome
            if any(i.nome == nome for i in self.ingredientes):
                messagebox.showerror("Erro", "Já existe um ingrediente com este nome!")
                return
                
            novo_ing = Ingrediente(nome, carb, prot, gord, fibra, sodio)
            self.ingredientes.append(novo_ing)
        
        # Salvar e atualizar interface
        DataManager.salvar_ingredientes(self.ingredientes)
        self._atualizar_combos()
        messagebox.showinfo("Sucesso", "Ingrediente salvo com sucesso!")
        self._novo_ingrediente()
    
    def adicionar_ingrediente_receita(self):
        # Validação
        ingrediente_nome = self.combo_ingredientes.get()
        quantidade = self.entry_quantidade.get()
        
        if not ingrediente_nome or not quantidade:
            messagebox.showerror("Erro", "Selecione um ingrediente e digite a quantidade")
            return
        
        # Adicionar à lista
        self.lista_ingredientes.insert(
            'end', 
            f"{ingrediente_nome} - {quantidade}g\n"
        )
    
    def salvar_receita(self):
        try:
            rendimento_total = float(self.entry_rendimento_total.get())
            if rendimento_total <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Rendimento total deve ser um número positivo")
            return

        nome = self.entry_nome_receita.get()
        ingredientes_texto = self.lista_ingredientes.get('1.0', 'end').strip()

        if not nome or not ingredientes_texto:
            messagebox.showerror("Erro", "Preencha todos os campos")
            return

        # Processar ingredientes
        ingredientes = []
        for line in ingredientes_texto.split('\n'):
            if not line:
                continue
            try:
                nome_ing, resto = line.split(' - ')
                quantidade = int(resto.replace('g', '').strip())
                ingrediente = next(i for i in self.ingredientes if i.nome == nome_ing)
                ingredientes.append((ingrediente, quantidade))
            except Exception as e:
                messagebox.showerror("Erro", f"Formato inválido na linha: {line}")
                return

        if self.receita_selecionada:
            # Modo edição
            self.receita_selecionada.nome = nome
            self.receita_selecionada.ingredientes = ingredientes
            self.receita_selecionada.rendimento_total = rendimento_total
        else:
            # Modo nova receita
            if any(r.nome == nome for r in self.receitas):
                messagebox.showerror("Erro", "Já existe uma receita com este nome!")
                return
                
            nova_receita = Receita(
                nome=nome,
                ingredientes=ingredientes,
                rendimento_total=rendimento_total  # Parâmetro obrigatório
            )
            self.receitas.append(nova_receita)

        DataManager.salvar_receitas(self.receitas)
        self._atualizar_combos_receitas()
        messagebox.showinfo("Sucesso", "Receita salva com sucesso!")
        self._nova_receita()

    def _deletar_ingrediente(self):
        nome = self.combo_ingredientes_exist.get()
        if not nome:
            return
        
        resposta = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o ingrediente '{nome}'?\nEsta ação não pode ser desfeita!"
        )
        if not resposta:
            return
        
        # Remover ingrediente
        ingrediente = next((i for i in self.ingredientes if i.nome == nome), None)
        if ingrediente:
            self.ingredientes.remove(ingrediente)
            
            # Remover de todas as receitas
            for receita in self.receitas:
                receita.ingredientes = [
                    (ing, qtd) for ing, qtd in receita.ingredientes 
                    if ing.nome != nome
                ]
            
            DataManager.salvar_ingredientes(self.ingredientes)
            DataManager.salvar_receitas(self.receitas)
            self._atualizar_combos()
            self._novo_ingrediente()
            messagebox.showinfo("Sucesso", "Ingrediente excluído com sucesso!")

    def _deletar_receita(self):
        nome = self.combo_receitas_exist.get()
        if not nome:
            return
        
        resposta = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir a receita '{nome}'?\nEsta ação não pode ser desfeita!"
        )
        if not resposta:
            return
        
        # Remover receita
        receita = next((r for r in self.receitas if r.nome == nome), None)
        if receita:
            self.receitas.remove(receita)
            
            DataManager.salvar_receitas(self.receitas)
            self._atualizar_combos_receitas()
            self._nova_receita()
            messagebox.showinfo("Sucesso", "Receita excluída com sucesso!")
    
    def gerar_pdf(self):
        # Coletar receitas e porções
        receitas_porcoes = []
        peso_total = 0.0

        for frame in self.frame_receitas.winfo_children():
            children = frame.winfo_children()
            if len(children) >= 2:
                nome_receita = children[0].get()
                quantidade = children[1].get()
                
                if nome_receita and quantidade:
                    receita = next(r for r in self.receitas if r.nome == nome_receita)
                    peso_total += float(quantidade)  # Calcular peso total
                    receitas_porcoes.append((receita, float(quantidade)))
        
        if not receitas_porcoes:
            messagebox.showerror("Erro", "Adicione pelo menos uma receita")
            return
        
        # Calcular e gerar PDF
        dados = CalculadoraNutricional.calcular_por_porcao(receitas_porcoes)
        nome_arquivo = f"Tabela_Nutricional_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        GeradorPDF.gerar_tabela_nutricional(nome_arquivo, dados, peso_total)
        messagebox.showinfo("Sucesso", f"PDF gerado: {nome_arquivo}")

if __name__ == "__main__":
    app = NutritionApp()
    app.mainloop()