from fpdf import FPDF

class PresentationPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, 'Projeto CondoFix - Apresentação', 0, 1, 'R')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def add_slide(self, title, content):
        self.add_page()
        # Slide Title
        self.set_font('Arial', 'B', 24)
        self.set_text_color(0, 51, 102) # Dark Blue
        self.cell(0, 20, title, 0, 1, 'L')
        self.ln(10)
        
        # Slide Content
        self.set_font('Arial', '', 14)
        self.set_text_color(0, 0, 0) # Black
        if isinstance(content, list):
            for item in content:
                self.multi_cell(0, 10, f'- {item}', 0, 'L')
                self.ln(2)
        else:
            self.multi_cell(0, 10, content, 0, 'L')

pdf = PresentationPDF(orientation='L', unit='mm', format='A4')
pdf.set_auto_page_break(auto=True, margin=15)

# --- Slide 1: Capa ---
pdf.add_page()
pdf.set_font('Arial', 'B', 32)
pdf.set_text_color(0, 51, 102)
pdf.ln(40)
pdf.cell(0, 20, 'CONDOFIX', 0, 1, 'C')
pdf.set_font('Arial', 'B', 18)
pdf.cell(0, 15, 'Sistema de Gestão de Manutenção Condominial', 0, 1, 'C')
pdf.ln(20)
pdf.set_font('Arial', '', 12)
pdf.set_text_color(0, 0, 0)
pdf.cell(0, 10, 'PÓS-GRADUAÇÃO LATO SENSU EM DESENVOLVIMENTO DE SISTEMAS COMPUTACIONAIS', 0, 1, 'C')
pdf.cell(0, 10, 'Disciplina: DESENVOLVIMENTO WEB', 0, 1, 'C')
pdf.ln(10)
pdf.set_font('Arial', 'B', 14)
pdf.cell(0, 10, 'Membro do Grupo: David Venancio da Silva Sousa', 0, 1, 'C')

# --- Slide 2: Contextualização ---
pdf.add_slide('Contextualização', [
    'Gestão de condomínios frequentemente enfrenta processos lentos e manuais.',
    'Dificuldade de rastreamento de solicitações de manutenção.',
    'Falta de transparência nos custos e prazos para os moradores.',
    'Necessidade de uma plataforma centralizada para comunicação entre moradores, técnicos e administradores.'
])

# --- Slide 3: Objetivo do Projeto ---
pdf.add_slide('Objetivo do Projeto', [
    'Desenvolver um sistema web moderno e intuitivo para gestão de ordens de serviço.',
    'Otimizar o fluxo de trabalho dos técnicos de manutenção.',
    'Fornecer ferramentas de auditoria e controle de custos para a administração.',
    'Garantir a segurança dos dados dos usuários conforme padrões OWASP.'
])

# --- Slide 4: Requisitos do Projeto ---
pdf.add_slide('Requisitos do Projeto', [
    'Funcionais: Cadastro de usuários (Morador, Técnico, Admin), Abertura de chamados com upload de imagens, Gestão de status de serviços, Painel de liderança com métricas.',
    'Não-Funcionais: Segurança profunda (CSRF, Talisman, Criptografia), Interface responsiva (Bootstrap 5), Performance com Cache, Processamento assíncrono de imagens.'
])

# --- Slide 5: Metodologia Empregada ---
pdf.add_slide('Metodologia Empregada', [
    'Desenvolvimento Ágil iterativo.',
    'Abordagem "Security-First" (Auditorias de segurança em cada etapa).',
    'Uso de padrões de design MVC (Model-View-Controller).',
    'Integração Contínua e validação rigorosa via Testes Unitários.'
])

# --- Slide 6: Ferramentas Empregadas ---
pdf.add_slide('Ferramentas Empregadas', [
    'Linguagem: Python 3.14',
    'Framework Web: Flask 3.0.3',
    'Persistência: SQLAlchemy & SQLite',
    'Segurança: Flask-Bcrypt, Flask-WTF, Flask-Talisman',
    'Frontend: HTML5, CSS3, Bootstrap 5, Jinja2',
    'Outros: Flask-Caching, Flask-Executor, Pytest'
])

# --- Slide 7: Benefícios da IA no Desenvolvimento ---
pdf.add_slide('Benefícios da Aplicação de IA', [
    'Aceleração significativa na geração de código boilerplate e templates.',
    'Auditoria automática de segurança identificando vulnerabilidades OWASP complexas.',
    'Auxílio na escrita e depuração de testes unitários.',
    'Sugestões inteligentes para refatoração e otimização de performance.'
])

# --- Slide 8: Dificuldades da IA no Desenvolvimento ---
pdf.add_slide('Dificuldades da Aplicação de IA', [
    'Necessidade de validação constante para evitar "alucinações" em lógicas de negócio.',
    'Dificuldade em gerenciar dependências de ambiente específicas (venv/pip) sem supervisão.',
    'Riscos de segurança se a IA sugerir padrões obsoletos ou inseguros sem revisão crítica.'
])

# --- Slide 9: Demonstração do Projeto ---
pdf.add_slide('Demonstração do Projeto', [
    'Portal do Morador: Interface simplificada para abertura e acompanhamento de chamados.',
    'Fila do Técnico: Visão clara das tarefas pendentes e em atendimento.',
    'Painel Administrativo: Dashboard com custo por setor e tempo médio de resolução.',
    'Segurança Integrada: Proteções CSRF e cabeçalhos de segurança ativos em todas as páginas.'
])

# --- Slide 10: Considerações Finais ---
pdf.add_slide('Considerações Finais', [
    'O CondoFix resolve problemas reais de gestão condominial com foco em segurança.',
    'A tecnologia Flask mostrou-se ideal para um desenvolvimento rápido e modular.',
    'O uso estratégico de IA permitiu entregar um produto robusto em tempo recorde.',
    'O sistema está pronto para produção, seguindo as melhores práticas do mercado.'
])

# --- Slide 11: Trabalhos Futuros ---
pdf.add_slide('Trabalhos Futuros', [
    'Desenvolvimento de aplicativo móvel nativo.',
    'Integração com sensores IoT para manutenção preditiva automática.',
    'Módulo de inteligência artificial para análise de sentimentos em feedbacks de moradores.',
    'Sistema de pagamentos integrado para custos de manutenção.'
])

pdf.output('apresentacao_condofix.pdf')
