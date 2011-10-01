#!/usr/bin/env python
#coding: utf-8 

import sys, re, time
from PyQt4 import uic
from PyQt4 import QtGui
from PyQt4 import QtSql
from PyQt4 import QtCore
from pysqlite2 import dbapi2 as sqlite3

class CadEmpresaProduto(QtCore.QObject):

	empresaSelecionada = ''
	ui = None

	def __init__(self, uifile, desktop):
		
		# inicializa banco de dados
		CadEmpresaProduto.db = sqlite3.connect("db/mercado_albino.db")
		cur = CadEmpresaProduto.db.cursor()
		try:
			cur.execute("Select codigo from Empresa") 
			cur.close()
		except sqlite3.Error, e: 
			try: 
			  cur.executescript("""
			     CREATE TABLE Empresa(codigo INTEGER PRIMARY KEY, nome TEXT, cnpj TEXT, telefone TEXT);
			     CREATE TABLE Produto(codigo INTEGER PRIMARY KEY, cod_empresa, produto, 
			                          preco_custo, margem_lucro, preco_venda); """)
			 
			  CadEmpresaProduto.db.commit()
			  cur.close()
			except sqlite3.Error, e: 
				print "Erro ao criar base de dados: ", e.args[0]

		CadEmpresaProduto.ui = uic.loadUi(uifile)
		
		CadEmpresaProduto.avail_width = (desktop.screenGeometry()).width()
		CadEmpresaProduto.avail_height = (desktop.screenGeometry()).height()

		# centraliza tela
		CadEmpresaProduto.centralizaform(CadEmpresaProduto.ui)

		self.cademp = CadEmpresa()
		self.cadprod = CadProduto()
		CadEmpresaProduto.ui.show() 
	
	@staticmethod
	def centralizaform(widget):
		widget.move ( (CadEmpresaProduto.avail_width - widget.width())/2,  (CadEmpresaProduto.avail_height - widget.height())/2)
	
	@staticmethod
	def isNumber(nr):
	    try:
	       int(nr)
	    except ValueError:
	       return False
	    return True
    	
	@staticmethod
	def messageBoxInfo(msg):
             msgBox = QtGui.QMessageBox()
	     msgBox.setIcon(QtGui.QMessageBox.Information)
	     msgBox.setText(msg);
	     msgBox.setStandardButtons(QtGui.QMessageBox.Ok)
     	     msgBox.setDefaultButton(QtGui.QMessageBox.Ok)
     	     msgBox.setWindowTitle("Aviso")
	     return msgBox.exec_()

class CadEmpresa(QtCore.QObject): 
	
	def __init__(self):
		
		self.modo = 0
		self.empresa = -1
		self.widgets =  { 'codigo' :  CadEmpresaProduto.ui.lineEdit, 
				  'cnpj'   :  CadEmpresaProduto.ui.lineEdit_2, 
				  'nome'   :  CadEmpresaProduto.ui.lineEdit_3,  
				  'telefone' : CadEmpresaProduto.ui.lineEdit_4 } 

		self.keys = ['codigo', 'cnpj', 'nome', 'telefone']
		self.dataEmpresa = {}
		for key in self.keys: 
			self.dataEmpresa[key] = []

		self.connect(CadEmpresaProduto.ui.pushButton_5, QtCore.SIGNAL('clicked(bool)'), self.cadastrar)
		self.connect(CadEmpresaProduto.ui.pushButton_6, QtCore.SIGNAL('clicked(bool)'), self.editar)
		self.connect(CadEmpresaProduto.ui.pushButton_10, QtCore.SIGNAL('clicked(bool)'), self.excluir)
		self.connect(CadEmpresaProduto.ui.pushButton_4, QtCore.SIGNAL('clicked(bool)'),  self.anterior)
		self.connect(CadEmpresaProduto.ui.pushButton_3, QtCore.SIGNAL('clicked(bool)'),  self.proxima)
		self.connect(CadEmpresaProduto.ui.pushButton_12, QtCore.SIGNAL('clicked(bool)'),  self.pesquisar)
		
		cur = CadEmpresaProduto.db.cursor()
		cur.execute("Select * from Empresa order by codigo asc")
		firstemp = cur.fetchone()
		if firstemp:
			CadEmpresaProduto.empresaSelecionada = self.valorlinha('codigo', firstemp) 
			for key in self.keys:
			  (self.dataEmpresa[key]).append( self.valorlinha (key, firstemp) )
			for emp in cur.fetchall():
				for key in self.keys:
				  (self.dataEmpresa[key]).append( self.valorlinha (key, emp) )
		cur.close()
	
		self.pesquisarui = uic.loadUi("ui/FiltroEmpresa.ui")
		self.connect(self.pesquisarui.pushButton, QtCore.SIGNAL('clicked(bool)'),  self.pesquisar)
		self.connect(self.pesquisarui.pushButton_2, QtCore.SIGNAL('clicked(bool)'),  self.fechapesquisar)

		# Menu Empresa actions
		self.connect(CadEmpresaProduto.ui.actionCad, QtCore.SIGNAL('activated()'), self.cadastrar)
		self.connect(CadEmpresaProduto.ui.actionCad, QtCore.SIGNAL('activated()'), self.atualizaTableView)
		self.connect(CadEmpresaProduto.ui.actionEditar, QtCore.SIGNAL('activated()'), self.editar)
		self.connect(CadEmpresaProduto.ui.actionExcluir, QtCore.SIGNAL('activated()'), self.excluir)
		self.connect(CadEmpresaProduto.ui.actionPesquisar, QtCore.SIGNAL('activated()'), self.pesquisar)
		
		self.inicializaform()

	def valorlinha(self, key, row):

		(cod, nome, cnpj, telefone) = row 
		if key == 'codigo':
			return "%s" % cod	
		elif key == 'nome':
			return "%s" % nome
		elif key == 'cnpj':
			return "%s" % cnpj
		elif key == 'telefone':
			return "%s" % telefone
	
	def inicializaform(self):

		if not self.basevazia(): 
			self.proxima()
		return 
		

	def basevazia(self):

		cur = CadEmpresaProduto.db.cursor()
		cur.execute("Select * from Empresa")
		firstemp = cur.fetchone()
		cur.close()
		if firstemp:
			return False
		return True
			

	def criaelem(self):

		return ('%s' % (self.widgets['nome']).text(), '%s' %(self.widgets['cnpj']).text(),'%s' % (self.widgets['telefone']).text(),)

	def cadastrar(self):

		if self.modo == 0:
		    self.modo = 1
		    self.limpaform()
		    self.enableform()
		    (self.widgets['codigo']).setText("%s" % self.proximocodemp())
		    (self.widgets['codigo']).setEnabled(False)
		    (self.widgets['cnpj']).setFocus(QtCore.Qt.MouseFocusReason)
#		    self.formprodui.lineEdit_2.setText("")
#		    self.formprodui.lineEdit_2.home()
	    	    CadEmpresaProduto.empresaSelecionada = None
	    	elif self.modo == 1:
		    self.modo = 0
		    self.empresa = len(self.dataEmpresa['codigo'])
#		    empresa = (self.widgets['codigo']).text()
#		    if empresa in (self.dataEmpresa['codigo']): 
#			print "Informe outro Codigo"
#		    else:
	            for key in self.keys:
			    (self.dataEmpresa[key]).append((self.widgets[key]).text()) 
		    self.updateDB("inserir")    
		    self.disableform()
		    CadEmpresaProduto.empresaSelecionada = (self.widgets['codigo']).text()

	def editar(self):

		if self.modo == 0 and self.dataEmpresa['codigo'] <> []:
			self.modo = 2
		        self.enableform()
		    	(self.widgets['cnpj']).setFocus(QtCore.Qt.MouseFocusReason)
		elif self.modo == 2:
		    self.modo = 0
		    empresa = (self.widgets['codigo']).text()
   		    if empresa in (self.dataEmpresa['codigo']): 
		        idx = (self.dataEmpresa['codigo']).index(empresa)
		        for key in self.keys:
			  (self.dataEmpresa[key])[idx] = (self.widgets[key]).text()
		    self.updateDB("atualizar")    
		    self.disableform()

	def excluir(self):

	    if self.modo == 0:
	    	if self.avisoExcluir() == QtGui.QMessageBox.RejectRole: 
			return 
		empresa = (self.widgets['codigo']).text()
		if empresa in (self.dataEmpresa['codigo']): 
		    idx = (self.dataEmpresa['codigo']).index(empresa)
		    # exclui unico da lista
		    if len(self.dataEmpresa['codigo']) == 1:
			 for key in self.keys:
			    self.dataEmpresa[key] = []
		    #exclui do comeco da lista
		    elif idx == 0: 
		        for key in self.keys:
			    self.dataEmpresa[key] = self.dataEmpresa[key][1:]
		    #excluiu a ultima  da lista
		    elif idx+1 == len(self.dataEmpresa['codigo']): 
			for key in self.keys: 
			    (self.dataEmpresa[key]).pop()
		     #excluiu uma do meio da lista
		    else: 
		        for key in self.keys: 
			    self.dataEmpresa[key] = self.dataEmpresa[key][:idx] + self.dataEmpresa[key][idx+1:]
		    #atualiza form apos exclusao
		    if self.dataEmpresa['codigo'] == []:   
		         self.limpaform()
                         self.empresa = -1
			 CadEmpresaProduto.empresaSelecionada = None
		    else: 
			 if self.empresa > len(self.dataEmpresa['codigo'])-1:
			     self.empresa -= 1
                         CadEmpresaProduto.empresaSelecionada = self.dataEmpresa['codigo'][self.empresa]
			 self.atualizaform()

		    self.updateDB("excluir", empresa)

	def avisoExcluir(self):

             msgBox = QtGui.QMessageBox()
	     msgBox.setIcon(QtGui.QMessageBox.Warning)
	     msgBox.setWindowTitle(u"Excluir Empresa")
	     msgBox.setText(u"Aviso:\nTodos os produtos desta empresa serão excluídos.\nDeseja continuar ?")
#	     msgBox.setInformativeText("Do you want to save your changes?")
#	     msgBox.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
	     msgBox.addButton(u"OK", QtGui.QMessageBox.AcceptRole) 
	     msgBox.addButton(u"Cancelar", QtGui.QMessageBox.RejectRole) 
#	     msgBox.setDefaultButton(QtGui.QMessageBox.AcceptRole)
	     return msgBox.exec_()

	def pesquisar(self):

		if self.modo == 0:
			self.limpaformpesquisar()
			CadEmpresaProduto.centralizaform(self.pesquisarui)
			self.pesquisarui.show()
		       	self.pesquisarui.activateWindow()
			self.pesquisarui.lineEdit_4.setFocus(QtCore.Qt.MouseFocusReason)
			self.modo = 1
		elif self.modo == 1:
			codnome = self.pesquisarui.lineEdit_4.text()
			empresaidx = -1
			if CadEmpresaProduto.isNumber(codnome):
				try: 
					array = self.dataEmpresa['codigo']
					empresaidx = array.index(codnome)
				except:
					pass

			else:
				array = self.dataEmpresa['nome']
				idx = 0
				for emp in array:
					expunicode = re.compile(r'' + unicode(str(codnome)) + '.*', re.UNICODE)			
					if expunicode.match(unicode(emp)):
						empresaidx = idx
						break
					idx += 1		

			self.pesquisarui.close()
			self.modo = 0
			if empresaidx > -1:
				self.empresa = empresaidx
				self.atualizaform()
				CadEmpresaProduto.empresaSelecionada = self.dataEmpresa['codigo'][empresaidx]
				self.atualizaTableView()
			else:
				CadEmpresaProduto.messageBoxInfo(u"Empresa não encontrada!")

	def  fechapesquisar(self):
		self.pesquisarui.close()
		self.modo = 0

    	def limpaformpesquisar(self):
		self.pesquisarui.lineEdit_4.setText("")

	def proxima(self):
	    if self.modo == 0 and self.empresa < len(self.dataEmpresa['codigo'])-1:
		self.empresa += 1
		self.atualizaform()

	def anterior(self):
	    if self.modo == 0 and self.empresa > 0:
		self.empresa -= 1
		self.atualizaform()

	def limpaform(self):
		for key in self.keys:
		    (self.widgets[key]).setText("")

	def disableform(self):
		for key in self.keys:
		    (self.widgets[key]).setEnabled(False)

	def enableform(self):
		for key in self.keys:
			if key != 'codigo': 
			    (self.widgets[key]).setEnabled(True)
	
	def atualizaform(self):
		CadEmpresaProduto.empresaSelecionada = self.dataEmpresa['codigo'][self.empresa] 
		for key in self.keys:
		    (self.widgets[key]).setText( (self.dataEmpresa[key])[self.empresa] )

	def proximocodemp(self):
		cur = CadEmpresaProduto.db.cursor()
		try: 
			cur.execute("Select codigo from Empresa order by codigo desc")
			(codemp,) = cur.fetchone()
			if codemp:
				codemp += 1
			else:
				codemp = 1
		except:
			codemp = 1	
		cur.close()
		return codemp

	def updateDB(self, operacao, codigo=None):
		
		cur = CadEmpresaProduto.db.cursor()
		if operacao == "inserir":
		    	cur.execute("Insert into Empresa (nome, cnpj, telefone) values (?,?,?)", self.criaelem())
		elif operacao == "excluir": 
		    	cur.execute("Delete from Empresa where codigo = ?", (int(codigo),))
		    	cur.execute("Delete from Produto where cod_empresa = ?", (int(codigo),))
			#Delete from Produto where codigo = ?
		elif operacao == "atualizar": 
			codigo = (self.widgets['codigo']).text()
		    	nome = (self.widgets['nome']).text()
		    	cnpj = (self.widgets['cnpj']).text()
		    	telefone = (self.widgets['telefone']).text()
		    	cur.execute("Update Empresa set nome = ?, cnpj = ?, telefone = ? where codigo = ?", ("%s" % nome, "%s" % cnpj, "%s" % telefone, int(codigo),))
		CadEmpresaProduto.db.commit()

	def atualizaTableView(self):
		
		self.dataProdutosEmpresa = []
		if CadEmpresaProduto.empresaSelecionada: 
			cur = CadEmpresaProduto.db.cursor()
			for prod in cur.execute("Select * from Produto where cod_empresa = ? order by produto asc", (int(CadEmpresaProduto.empresaSelecionada),)):
				self.dataProdutosEmpresa.append(prod) 
       			cur.close() 
		CadEmpresaProduto.tbviewmodel = ProdutoModel(self.dataProdutosEmpresa, [u'Cód. Produto',u'Cód. Empresa', u'Produto', u'Preço de Custo', u'Margem Lucro', u'Preço Venda'],None)
		CadEmpresaProduto.ui.tableView.setModel( CadEmpresaProduto.tbviewmodel )


class CadProduto(QtCore.QObject):
    
	def __init__(self):
	
		self.formprodui = uic.loadUi("ui/CadProd.ui")
		self.edtformprodui = uic.loadUi("ui/EditProd.ui")
		self.dataProdutos = []
		self.dataProdutosEmpresa = []

		#Produtos da Primeira Empresa
		self.atualizaTableView()

		# resize column product 
		CadEmpresaProduto.ui.tableView.setColumnWidth(2,239)
		CadEmpresaProduto.ui.tableView.setWordWrap(True)
		CadEmpresaProduto.ui.tableView.resizeRowsToContents()
#		CadEmpresaProduto.ui.tableView.setShowGrid(False)

		#from main form cadprod 
		self.connect(CadEmpresaProduto.ui.pushButton, QtCore.SIGNAL('clicked(bool)'), self.cadastrar)
		self.connect(CadEmpresaProduto.ui.pushButton_13, QtCore.SIGNAL('clicked(bool)'), self.imprimir)
		self.connect(CadEmpresaProduto.ui.pushButton_11, QtCore.SIGNAL('clicked(bool)'), self.excluir)
		self.connect(CadEmpresaProduto.ui.pushButton_2, QtCore.SIGNAL('clicked(bool)'), self.editar)
		self.connect(CadEmpresaProduto.ui.pushButton_7, QtCore.SIGNAL('clicked(bool)'),  self.pesquisar)

		# from form cadempresa
		self.connect(CadEmpresaProduto.ui.pushButton_5, QtCore.SIGNAL('clicked(bool)'), self.atualizaTableView)
		self.connect(CadEmpresaProduto.ui.pushButton_4, QtCore.SIGNAL('clicked(bool)'), self.atualizaTableView)
  		self.connect(CadEmpresaProduto.ui.pushButton_3, QtCore.SIGNAL('clicked(bool)'), self.atualizaTableView)
		self.connect(CadEmpresaProduto.ui.pushButton_10, QtCore.SIGNAL('clicked(bool)'), self.atualizaTableView)

		# form form cadprod 
		self.connect(self.formprodui.pushButton_2, QtCore.SIGNAL('clicked(bool)'), self.cadastrar)
		self.connect(self.formprodui.lineEdit, QtCore.SIGNAL('textEdited(const QString &)'), self.calculaprecovenda_percent )
		self.connect(self.formprodui.lineEdit_4, QtCore.SIGNAL('textEdited(const QString &)'), self.calculaprecovenda_valor )
		self.connect(self.formprodui.pushButton, QtCore.SIGNAL('clicked(bool)'), self.fechaformcadastrar)
		
		self.connect(self.edtformprodui.pushButton_2, QtCore.SIGNAL('clicked(bool)'), self.editar)
		self.connect(self.edtformprodui.lineEdit, QtCore.SIGNAL('textEdited(const QString &)'), self.calculaprecovenda_percentedt )
		self.connect(self.edtformprodui.lineEdit_4, QtCore.SIGNAL('textEdited(const QString &)'), self.calculaprecovenda_valoredt )
		self.connect(self.edtformprodui.pushButton, QtCore.SIGNAL('clicked(bool)'), self.fechaformeditar)
	
		# search	
		self.pesquisarui = uic.loadUi("ui/FiltroProdutos.ui")
		self.connect(self.pesquisarui.pushButton, QtCore.SIGNAL('clicked(bool)'),  self.pesquisar)
		self.connect(self.pesquisarui.pushButton_2, QtCore.SIGNAL('clicked(bool)'),  self.fechapesquisar)

		# Menu Produto Action
		self.connect(CadEmpresaProduto.ui.actionCadastrar, QtCore.SIGNAL('activated()'), self.cadastrar)
		self.connect(CadEmpresaProduto.ui.actionEditar_2, QtCore.SIGNAL('activated()'), self.editar)
		self.connect(CadEmpresaProduto.ui.actionExcluir_2, QtCore.SIGNAL('activated()'), self.excluir)
		self.connect(CadEmpresaProduto.ui.actionPesquisar_2, QtCore.SIGNAL('activated()'), self.pesquisar)
		self.connect(CadEmpresaProduto.ui.actionImprimir_Lista, QtCore.SIGNAL('activated()'), self.imprimirdlg)

		self.printdlg = 0
		self.modo = 0

	def cadastrar(self):
	
		if self.modo == 0: 
			
			self.limpaform()
			self.formprodui.lineEdit_3.setText("%s" % self.proximocodproduto())
			self.formprodui.lineEdit_3.setEnabled(False)
			CadEmpresaProduto.centralizaform(self.formprodui)
			self.formprodui.show()
			self.formprodui.lineEdit_2.setFocus(QtCore.Qt.MouseFocusReason)
			self.modo = 1
	
		elif self.modo == 1: #Editar 

#			dataProdutoAux = [] 
#			for prod in self.dataProdutos: 
#				if getcodprod(prod) <> prodselecionado:
#					dataProdutoAux.append(prod)
#				else:
#		    			self.dataProdutos.append( (self.formprodui.lineedit_3.text(),  
#					   self.formprodui.lineEdit_2.text(),  
#					   self.formprodui.lineEdit_4.text(),  
#					   self.formprodui.lineEdit.text(),  

#			self.dataProduto = []
#			self.dataProduto = dataProdutoAux

			self.updateDB("inserir")
			self.formprodui.close()
			self.atualizaTableView()
			self.modo = 0

	def  fechaformcadastrar(self):
		self.formprodui.close()
		self.modo = 0

	def criaelem(self, form):
		
		return	('%s' % CadEmpresaProduto.empresaSelecionada, 
				'%s' % 	   form.lineEdit_3.text(),  
				'%s' % 	   form.lineEdit_2.text(),  
				'%s' % 	   form.lineEdit_4.text(),  
				'%s' % 	   form.lineEdit.text(),  
				'%s' % 	   form.lineEdit_5.text()) 
	def editar(self):

		if self.modo == 0:
			prodidxselect = CadEmpresaProduto.ui.tableView.currentIndex()
			prod = CadEmpresaProduto.tbviewmodel.datarow (prodidxselect)
			if prod:
				self.edtformprodui.lineEdit_3.setText("%s" % prod[0])
			        self.edtformprodui.lineEdit_3.setEnabled(False)
				self.edtformprodui.lineEdit_2.setText("%s" % prod[2])
        		        self.edtformprodui.lineEdit_4.setText("%s" % prod[3])  
	        		self.edtformprodui.lineEdit.setText("%s" % prod[4])
			        self.edtformprodui.lineEdit_5.setText("%s" % prod[5])

				CadEmpresaProduto.centralizaform(self.edtformprodui)
				self.edtformprodui.show()
		        	self.edtformprodui.activateWindow()
				self.edtformprodui.lineEdit_2.setFocus(QtCore.Qt.MouseFocusReason)
				self.modo = 1
		elif self.modo == 1:
			self.updateDB("atualizar")
			self.edtformprodui.close()
			self.atualizaTableView()
			self.modo = 0

	def  fechaformeditar(self):
		self.edtformprodui.close()
		self.modo = 0

	def excluir(self):

		prodidxselect = CadEmpresaProduto.ui.tableView.currentIndex()
		prod = CadEmpresaProduto.tbviewmodel.datarow (prodidxselect)
		if prod:
			self.updateDB("excluir", prod)
			self.atualizaTableView()

	def indexprod(self, codprod):
		idx = 0 		
		for prod in self.dataProdutos:
			if codprod == getcodprod(prod):
				return idx
			idx += 1
		return -1 	

	def getcodprod(self, prod):
		(a0,x,a1,a2,a3,a4) = prod
		return x

	def getcodemp(self, emp):
		(x,a0,a1,a2,a3,a4) = emp
		return x

	def limpaform(self):

		self.formprodui.lineEdit_3.setText("")
	        self.formprodui.lineEdit_2.setText("")
                self.formprodui.lineEdit_4.setText("")  
	        self.formprodui.lineEdit.setText("")
	        self.formprodui.lineEdit_5.setText("")

	def atualizaform(self, codprod):

		(a0,a1,a2,a3,a4) = self.dataProduto[ indexprod(prodselecionado) ]
		self.formprodui.lineedit_3.setText("%s" % a0)
	        self.formprodui.lineedit_3.setEnabled(false)
		self.formprodui.lineEdit_2.setText("%s" % a1)
                self.formprodui.lineEdit_4.setText("%s" % a2)  
	        self.formprodui.lineEdit.setText("%s" % a3)
	        self.formprodui.lineEdit_5.setText("%s" % a4)
	
	def atualizaTableView(self):

		self.dataProdutosEmpresa = []
#		for prod in (self.dataProdutos):
#			if self.getcodemp(prod) == CadEmpresaProduto.empresaSelecionada:
#				self.dataProdutosEmpresa.append(prod)
		if CadEmpresaProduto.empresaSelecionada: 
			cur = CadEmpresaProduto.db.cursor()
			for prod in cur.execute("Select * from Produto where cod_empresa = ? order by produto asc", (int(CadEmpresaProduto.empresaSelecionada),)):
				self.dataProdutosEmpresa.append(prod) 
       			cur.close() 
		CadEmpresaProduto.tbviewmodel = ProdutoModel(self.dataProdutosEmpresa, [u'Cód. Produto',u'Cód. Empresa', u'Produto', u'Preço de Custo', u'Margem Lucro', u'Preço Venda'],None)
		CadEmpresaProduto.ui.tableView.setModel( CadEmpresaProduto.tbviewmodel )

	def precototal(self, percent, precocusto):
		if precocusto:
			precocusto_ = float ( precocusto )
		else:
			return 0.0
		if percent: 
			percent_ = float ( percent ) / 100.0 
		else:
			return precocusto_

		return (precocusto_ * percent_) + precocusto_

	def calculaprecovenda_valor(self, precocusto):
		total = self.precototal( self.formprodui.lineEdit.text(), precocusto )
		self.formprodui.lineEdit_5.setText("%s" % total) 

	def calculaprecovenda_percent(self, percent):
		total = self.precototal( percent, self.formprodui.lineEdit_4.text() )
		self.formprodui.lineEdit_5.setText("%s" % total) 

	def calculaprecovenda_valoredt(self, precocusto):
		total = self.precototal( self.edtformprodui.lineEdit.text(), precocusto )
		self.edtformprodui.lineEdit_5.setText("%s" % total) 

	def calculaprecovenda_percentedt(self, percent):
		total = self.precototal( percent, self.edtformprodui.lineEdit_4.text() )
		self.edtformprodui.lineEdit_5.setText("%s" % total) 

	def calculaprecovendaedt(self, percent):

		precocusto = float ( self.edtformprodui.lineEdit_4.text() )
		percent = float ( percent ) / 100.0 
		total = (precocusto * percent) + precocusto
		self.edtformprodui.lineEdit_5.setText("%s" % total) 

	def proximocodproduto(self):
		cur = CadEmpresaProduto.db.cursor()
		try:
			cur.execute("Select codigo from Produto order by codigo desc")
			(codprod,) = cur.fetchone()
			if codprod:
				codprod += 1
			else:
				codprod = 1
		except:
			codprod = 1
		cur.close()
		return codprod

	def imprimirdlg(self):
		self.printdlg = 1
		self.imprimir()

	def imprimir(self):

		if CadEmpresaProduto.empresaSelecionada < 1: 
			CadEmpresaProduto.messageBoxInfo("Nenhuma empresa selecionada.")
			return 
		
		#Cabecalho
		listprod = QtGui.QTextDocument()
		doccursor = QtGui.QTextCursor(listprod)
		self.configuraCabecalho(doccursor)	
		# print listprod.size().height()

		#Colunas da Tabela de Produtos
		tb = self.configuraTabela(doccursor)
		# print listprod.size().height()

		#Corpo da Tabela de Produtos 
		self.imprimeCorpoTabela(tb, listprod)
		# print listprod.size().height()
		
		# Imprime
		printer = QtGui.QPrinter()
		# printer.setOutputFormat(QtGui.QPrinter.PdfFormat)
		# printer.setOutputFileName("/home/rafael/albino.pdf")
		if self.printdlg: 	
			printDialog = QtGui.QPrintDialog(printer, CadEmpresaProduto.ui.centralwidget) 
			printDialog.setWindowTitle("Imprimir lista de produtos")
			printDialog.setWindowIcon(QtGui.QIcon("png/16x16/printer.png"))
			if (printDialog.exec_() == QtGui.QDialog.Accepted):
				listprod.print_(printer)
			self.printdlg = 0
		else: 
		 	listprod.print_(printer)

	def configuraCabecalho(self, doccursor):

		cur = CadEmpresaProduto.db.cursor()
		try:
			cur.execute("Select nome from Empresa where codigo = ?", (int(CadEmpresaProduto.empresaSelecionada),))
		except: 
			print "Empresa nao Encontrada"
			cur.close()
			return 

		txtformat = QtGui.QTextCharFormat()
		ft = QtGui.QFont("Arial")
		txtformat.setFont(ft)
		txtformat.setFontPointSize(10)
		emp = cur.fetchone()
		data = time.localtime()
		doccursor.insertText("Mercado Albino - %s/%s/%s\n" % ( data[2] , data[1] , data[0]), txtformat )
		doccursor.insertText("Lista de Produtos da Empresa: ", txtformat )
		ft.setBold(True) 
		txtformat.setFont(ft)
		doccursor.insertText("%s\n\n" % emp[0], txtformat)
		cur.close()


	def configuraTabela(self, doccursor):


		tbformat = QtGui.QTextTableFormat()
		tbformat.setColumnWidthConstraints([  	QtGui.QTextLength(QtGui.QTextLength.VariableLength, 0), 
							QtGui.QTextLength(QtGui.QTextLength.FixedLength, 200) ] + 
							[ QtGui.QTextLength() for i in range(0,3) ] )
		tbformat.setCellSpacing(1.0)
		tbformat.setCellPadding(0.0)
		tbformat.setBorder(0.0)
		
		tb = doccursor.insertTable(1,5, tbformat)

		txtformat = QtGui.QTextCharFormat()
		ft = QtGui.QFont("Arial")
		ft.setBold(True) 
		txtformat.setFont(ft)
		txtformat.setFontPointSize(10)

		self.imprimeColunas(0, tb,txtformat)

		return tb

	def imprimeColunas(self, row, tb, txtformat):

		cellformat = QtGui.QTextTableFormat()
 		brush = QtGui.QBrush(QtGui.QColor(235,235,235))
		cellformat.setBackground(brush)
		cellformat.setCellPadding(2.0)
		cellformat.setCellSpacing(0.0)
		cellformat.setBorder(0.0)
		cellformat.setColumnWidthConstraints([ QtGui.QTextLength(QtGui.QTextLength.PercentageLength, 100)])

#		cellcursor = tb.cellAt(0,0).firstCursorPosition()
#		cellcursor.insertText("Empresa", txtformat)

		cellcursor = tb.cellAt(row,0).firstCursorPosition()
		tbb = cellcursor.insertTable(1,1)
		tbb.setFormat(cellformat)
		cell = tbb.cellAt(0,0)
		cellcursor = cell.firstCursorPosition()
		cellcursor.insertText(u"Código\n", txtformat)

		cellcursor = tb.cellAt(row,1).firstCursorPosition()
		tbb = cellcursor.insertTable(1,1)
		tbb.setFormat(cellformat)
		cell = tbb.cellAt(0,0)
		cellcursor = cell.firstCursorPosition()
		cellcursor.insertText(u"Produto\n", txtformat)

		cellcursor = tb.cellAt(row,2).firstCursorPosition()
		tbb = cellcursor.insertTable(1,1)
		tbb.setFormat(cellformat)
		cell = tbb.cellAt(0,0)
		cellcursor = cell.firstCursorPosition()
		cellcursor.insertText(u"Preço de Custo", txtformat)

		cellcursor = tb.cellAt(row,3).firstCursorPosition()
		tbb = cellcursor.insertTable(1,1)
		tbb.setFormat(cellformat)
		cell = tbb.cellAt(0,0)
		cellcursor = cell.firstCursorPosition()
		cellcursor.insertText(u"Margem de Lucro %", txtformat)

		cellcursor = tb.cellAt(row,4).firstCursorPosition()
		tbb = cellcursor.insertTable(1,1)
		tbb.setFormat(cellformat)
		cell = tbb.cellAt(0,0)
		cellcursor = cell.firstCursorPosition()
		cellcursor.insertText(u"Preço de Venda", txtformat)

	def imprimeCorpoTabela(self, tb, doc):		
		
		# variables to control table header printing on each page
		# maxHeightDoc = 945.0
		# heightHeader = 84.0
		# heightTableHeader = 44.0
		# heightRow = 22.0
		# heightDoc = heightHeader + heightTableHeader 
		# chrColumnCapacity = 50 

		cur = CadEmpresaProduto.db.cursor()
		try: 
			cur.execute("Select codigo,produto,preco_custo,margem_lucro,preco_venda from Produto where cod_empresa = ? order by produto asc", (int(CadEmpresaProduto.empresaSelecionada),))
		except: 
			print ""
			return

		row = 1
		cor = 0
			
		cellformat = QtGui.QTextTableFormat()
		colorA = QtGui.QColor(240,240,240)
		colorB = QtGui.QColor(248,248,248)
		brushA = QtGui.QBrush(colorA)
		brushB = QtGui.QBrush(colorB)
		cellformat.setBackground(brushA)
		cellformat.setCellPadding(1.0)
		cellformat.setCellSpacing(1.0)
		cellformat.setBorder(0.0)
		cellformat.setHeight(QtGui.QTextLength(QtGui.QTextLength.PercentageLength, 100))
		
		# total = cur.count()
		for prod in cur.fetchall():
			tb.insertRows(row,1)
			for i in range(0,5): 
				cell =  tb.cellAt(row,i)
				cellcursor = cell.firstCursorPosition()
				if cor: 
					cellformat.setBackground(brushB)
				else:
					cellformat.setBackground(brushA)
				
				if i == 1: 
					cellformat.setColumnWidthConstraints([ QtGui.QTextLength(QtGui.QTextLength.FixedLength, 340) ])
				else:
					cellformat.setColumnWidthConstraints([ QtGui.QTextLength(QtGui.QTextLength.PercentageLength, 100)])
				
				# Not working!!
				if i == 0:
					cellformat.setAlignment(QtCore.Qt.AlignHCenter)
				elif i > 1: 
					cellformat.setAlignment(QtCore.Qt.AlignRight)

				tbb = cellcursor.insertTable(1,1)
				tbb.setFormat(cellformat)
				cell = tbb.cellAt(0,0)
				cellcursor = cell.firstCursorPosition()

				if i == 2 or i == 4 :
					preco = "%s" % prod[i] 
					if '.' in preco:
					    if len(preco.split('.')[1]) < 2:
					       preco = preco + '0'
					else:
					       preco = preco + '.00'
					cellcursor.insertText(preco)
				else:
					cellcursor.insertText("%s" % prod[i])

#			print doc.size().height() docsize couldn't used because of performance issues 
#			It was tried to access this property as less times as possible but it didnt work
#			prodcl =  self.larguraProdColumn(prod[1]) 
#			if prodcl > 340:
#				linhasMais = prodcl / 340
#				if prodcl % 340: 
#					linhasMais += 1 
#				heightDoc += (heightRow * linhasMais) 
#				print linhasMais
#			else: 
#				heightDoc += heightRow 

#			if maxHeightDoc < heightDoc:
#				txtformat = QtGui.QTextCharFormat()
#				ft = QtGui.QFont("Arial")
#				ft.setBold(True) 
#				txtformat.setFont(ft)
#				txtformat.setFontPointSize(10)
#				row += 1 
#				tb.insertRows(row,1)
#				self.imprimeColunas(row, tb, txtformat)
#				heightDoc = heightTableHeader

			if cor: 
				cor = 0
			else:
				cor = 1
			row += 1

#		fmformat = tb.frameFormat()
#		txtlenght = fmformat.value(0)
#		print txtlenght.rawValue()
		cur.close()

		# cellconf (cellconfig, fontconfig, content, parent_table, position)
	def larguraProdColumn(self, prod):
#		50 6.8  uppers proportion
#		40 8.5
		total = 0
		for char in prod:
			if unicode.islower(char):
				total += 7
			else:
				total += 9
		return total


	def pesquisar(self):
	
		if self.modo == 0:
			self.limpaformpesquisar()
			CadEmpresaProduto.centralizaform(self.pesquisarui)
			self.pesquisarui.show()
		       	self.pesquisarui.activateWindow()
			self.pesquisarui.lineEdit_4.setFocus(QtCore.Qt.MouseFocusReason)
			self.modo = 1
		elif self.modo == 1:
			codnome = self.pesquisarui.lineEdit_4.text()
			found = 0 
			if CadEmpresaProduto.isNumber(codnome):
				column=0
			else:
				column=2
			for row in range(0,CadEmpresaProduto.tbviewmodel.rowCount_()):
				idx = CadEmpresaProduto.tbviewmodel.index (row, column, QtCore.QModelIndex())
				prod = CadEmpresaProduto.tbviewmodel.data(idx, QtCore.Qt.DisplayRole)
#				if prod.toString() == str(codnome):
				if (column==0 and prod.toString() == str(codnome)) or \
			   	   (column==2 and re.match(r'' + str(codnome) + '.*', prod.toString())): 
					found = 1
					CadEmpresaProduto.ui.tableView.selectRow(row)
					break
			self.pesquisarui.close()
			self.modo = 0
			if not found:
				CadEmpresaProduto.messageBoxInfo(u"Produto não encontrado!")

	def  fechapesquisar(self):
		self.pesquisarui.close()
		self.modo = 0

    	def limpaformpesquisar(self):
		self.pesquisarui.lineEdit_4.setText("")

	def updateDB(self, operacao, prod=None):
		
		cur = CadEmpresaProduto.db.cursor()
		if operacao == "inserir":
			prod = self.criaelem(self.formprodui)
			cur.execute("Insert into Produto (cod_empresa, produto, preco_custo, margem_lucro, preco_venda) values (?,?,?,?,?)", (int(prod[0]), prod[2],prod[3],prod[4],prod[5],))
		elif operacao == "excluir": 
		    	cur.execute("Delete from Produto where codigo = ?", (int(prod[0]),))
		elif operacao == "atualizar": 
			prod = self.criaelem(self.edtformprodui)
		    	cur.execute("Update Produto set produto = ?, preco_custo = ?, margem_lucro = ?, preco_venda = ? where codigo = ?", (prod[2], prod[3],prod[4],prod[5],int(prod[1]),))
		CadEmpresaProduto.db.commit()


class ProdutoModel(QtCore.QAbstractTableModel):

	def __init__(self, datain, headerdata, parent=None, *args):
		QtCore.QAbstractTableModel.__init__(self, parent, *args)
		self.arraydata = datain
		self.headerdata = headerdata
	
	def rowCount(self, parent):
		return len(self.arraydata)
	
	def rowCount_(self):
		return len(self.arraydata)

	def columnCount(self, parent):
		return len(self.headerdata)

	def data(self, index, role):
		if not index.isValid():
			return QtCore.QVariant()
		elif role != QtCore.Qt.DisplayRole:
			return QtCore.QVariant()
		return  QtCore.QVariant(self.arraydata[index.row()][index.column()])

	def datarow(self, index):
		if index.row() == -1:
			return []		
		return  (self.arraydata[index.row()])

	def headerData(self, col, orientation, role):
	      if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
	          return QtCore.QVariant(self.headerdata[col])
	      return QtCore.QVariant()

if __name__ == "__main__":
	
	app = QtGui.QApplication(sys.argv)
	desktp = app.desktop()
	cademprod = CadEmpresaProduto("ui/CadaEmpProd.ui", desktp)
	sys.exit(app.exec_())
