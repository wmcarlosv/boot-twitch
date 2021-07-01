from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
import os
import json
import time
import sqlite3
import random
from datetime import datetime
import pandas as pd


def setLog(message=''):
	now = datetime.now()
	current_time = now.strftime("%d/%m/%Y %H:%M:%S")
	print("["+current_time+"] => "+message)

def getQuery(sql):
	response = ''
	try:
		cursor = con.cursor()
		cursor.execute(sql)
		response = cursor.fetchall()
		con.commit()
	except sqlite3.Error as er:
		setLog(str(er))

	return response

def setQuery(sql):
	response=''
	try:
		cursor = con.cursor()
		cursor.execute(sql)
		response = con.commit()
	except sqlite3.Error as er:
		setLog(str(er))

#DataBase
basePath = os.path.dirname(os.path.realpath(__file__)) + "/"
database = basePath + "twitch_users.db"
con = sqlite3.connect(database)
con.row_factory = sqlite3.Row

#Data
data = ''
jsonConfig = basePath + "config.json"
driver = basePath + "chromedriver.exe"
extension = basePath + "Block-image_v1.1.crx"
profile = basePath + "profile"

with open (jsonConfig) as fil:
	data = json.load(fil)

reloadBoot = True
totalChannelesByDelay = 0

def commentDynamic():
	comments = []
	totalComment = random.randint(4,5)
	excelFile = basePath + str(totalComment)+".xlsx"
	dataExcel = pd.read_excel(excelFile)

	for i in range(1, (totalComment+1)):
		df = pd.DataFrame(dataExcel, columns= [i])
		totalRows = len(df.values)
		selectedRow = random.randint(0, (int(totalRows)-1))
		comments.append(df.values[selectedRow][0])

	return comments

def setChannels(app):
	is_channels = False
	lastChannel = ""
	while is_channels == False:
		time.sleep(data['config']['delays']['delay_general'])
		try:
			channelUrl = ''
			channelText = ''
			channels = app.find_elements_by_class_name("ScTextWrapper-sc-14f6evl-1")
			setLog("Entrando a lista de Canales..")

			for channel in channels:
				try:
					childrenLink = channel.find_elements_by_tag_name("a")[0]
				except NoSuchElementException:
					break

				isSpanish = False

				try:
					childrenLang = channel.find_elements_by_tag_name("button")
					for cat in childrenLang:
						if cat.get_attribute("data-a-target") == 'Español' or cat.get_attribute("data-a-target") == 'Spanish':
							isSpanish = True
				except NoSuchElementException:
					isSpanish = False

				if isSpanish == True:
					if childrenLink.get_attribute("data-a-target") == 'preview-card-title-link':
						channelUrl = childrenLink.get_attribute("href")
						arrChannel = channelUrl.split("/")
						channelText = arrChannel[3]
						sql = "SELECT * FROM users WHERE url = '"+channelUrl+"'"
						if len(getQuery(sql)) <= 0:
							setChannel(app, channelUrl, channelText)
						else:
							setLog("El canal: "+channelUrl+", ya se encuentra en la base de datos..")
				else:
					setLog("El canal: "+str(childrenLink.get_attribute("href"))+", no es en Español, o no tiene etiquetas de idioma")
				
				#random channel sleep

			setLog("Saliendo de la Lista de Canales..")
			is_channels = True
				
		except NoSuchElementException:
			setLog("Esperando lista de Canales..")
			is_channels = False

	time.sleep(data['config']['delays']['delay_general'])

def setScrolls():
	scrolls = 0
	while scrolls <= int(data['config']['scrolling']):
		time.sleep(data['config']['delays']['delay_general'])
		setLog("Haciendo scroll: "+str(scrolls))
		app.execute_script('document.getElementsByClassName("ScCoreLink-udwpw5-0")[document.getElementsByClassName("ScCoreLink-udwpw5-0").length - 1].focus()')
		scrolls = scrolls + 1
		time.sleep(data['config']['delays']['delay_general'])


def setChannel(app, url, text):
	setLog("Entrando al canal: ["+url+"]")
	app.execute_script("window.open('')")
	app.switch_to.window(app.window_handles[1])
	app.get(url)
	isLive = True
	onlyFollowers = False

	time.sleep(data['config']['delays']['delay_general'])
	try:
		offline = app.find_elements_by_class_name("channel-status-info--offline")
		if len(offline) > 0:
			isLive = False
	except NoSuchElementException:
		isLive = False

	try:
		of = app.find_elements_by_class_name("chat-input-tray__clickable")
		if len(of) > 0:
			onlyFollowers = True
	except NoSuchElementException:
		onlyFollowers = False

	if isLive == True and onlyFollowers == False:
		if int(data['config']['pausar_stream']) == 1:
			try:
				plays = app.find_elements_by_tag_name("button")
				for play in plays:
					if play.get_attribute("data-a-target") == 'player-play-pause-button':
						setLog("Deteniendo el reproductor..")
						play.click()
						break

			except NoSuchElementException:
				setLog("Boton Play no Encontrado..")

		obj_textarea = ''
		try:
			textareas = app.find_elements_by_tag_name("textarea")
			for textarea in textareas:
				if textarea.get_attribute("data-a-target") == 'chat-input':
					obj_textarea = textarea
					break

		except NoSuchElementException:
			setLog("Caja de Mensaje no Encontrada..")

		cmts = commentDynamic()
		obj_textarea.click()

		time.sleep(data['config']['delays']['delay_general']);

		try:
			buttonsRules = app.find_elements_by_tag_name("button")
			for brs in buttonsRules:
				if brs.get_attribute("data-test-selector") == 'chat-rules-ok-button':
					setLog("boton de reglas encontrado..")
					brs.click()
					break

		except NoSuchElementException:
			setLog("Boton de Reglas no encontado..")

		time.sleep(data['config']['delays']['delay_general']);

		commentString = '['
		for cmt in cmts:
			comment_data = ''
			if str(cmt).find("@username") > 0:
				comment_data = str(cmt).replace("@username","@"+text)
			else:
				comment_data = str(cmt)

			commentString = commentString+comment_data+", "

			obj_textarea.send_keys(comment_data)

			setLog("Comentando: "+comment_data+", al canal ["+url+"]")

			time.sleep(data['config']['delays']['delay_general']);

			buttons = app.find_elements_by_tag_name("button")
			for button in buttons:
				if button.get_attribute("data-a-target") == 'chat-send-button':
					button.click()
					break

			startcmt = int(data['config']['delays']['delay_por_mensaje'][0])
			endcmt = int(data['config']['delays']['delay_por_mensaje'][1])
			time.sleep(random.randint(startcmt, endcmt))


		commentString = commentString.rstrip(commentString[-1])
		commentString = commentString+"]"

		sql = "INSERT INTO users (username,comentario, url, solo_seguidores) VALUES ('"+text+"','"+commentString+"','"+url+"',0)"
		setQuery(sql)
		setLog("Guardando en base de datos: [username=>"+text+", comentario=>"+commentString+", url=>"+url+", solo_seguidores=>0]")
	else:
		if onlyFollowers == True:
			sql = "INSERT INTO users (username,comentario, url, solo_seguidores) VALUES ('"+text+"','','"+url+"',1)"
			setQuery(sql)
			setLog("El canal: ["+url+"], es solo seguidores..")
		else:
			setLog("El canal: ["+url+"] no esta en linea..")
	
	#random channel sleep
	start = int(data['config']['delays']['delay_por_stream'][0])
	end = int(data['config']['delays']['delay_por_stream'][1])
	time.sleep(random.randint(start, end))
	setLog("Saliendo del canal: ["+url+"]")
	app.close()
	app.switch_to.window(app.window_handles[0])

session_id = ''

while reloadBoot == True:

	if session_id == '':
		#Start Boot
		chromeOptions = webdriver.ChromeOptions()
		chromeOptions.add_extension(extension)
		#chromeOptions.add_argument('headless')
		chromeOptions.add_argument("--user-data-dir="+profile);

		app = webdriver.Chrome(options=chromeOptions)
		app.get(data['config']['url_inicial'])
		session_id = app.session_id

	try:
		time.sleep(data['config']['delays']['delay_general']);
		#verify is login
		is_avatar = False
		try:
			avatar = app.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/nav/div/div[3]/div[6]/div/div/div/div/button/div/figure')
			is_avatar = True
		except NoSuchElementException:
			is_avatar = False

		if is_avatar == False:
			#Start Boot
			botonLogin = False
			while botonLogin == False:

				try:
					login_button = app.find_element(By.XPATH, '//*[@id="root"]/div/div[2]/nav/div/div[3]/div[3]/div/div[1]/div[1]/button')
					login_button.click()
					setLog("Click en el boton login")
					botonLogin = True
				except NoSuchElementException:
					botonLogin = False
					setLog("Esperando el boton login..")

				time.sleep(data['config']['delays']['delay_general']);

			login = False

			while login == False:
				try:
					user_name = app.find_element(By.XPATH,'//*[@id="login-username"]')
					user_name.send_keys(data['config']['username'])
					setLog("Enviando Usuario..")
					time.sleep(data['config']['delays']['delay_general'])

					password = app.find_element(By.XPATH, '//*[@id="password-input"]')
					password.send_keys(data['config']['password'])
					setLog("Enviando Clave..")
					time.sleep(data['config']['delays']['delay_general'])

					setLogin = app.find_element(By.XPATH,'/html/body/div[3]/div/div/div/div/div/div[1]/div/div/div[3]/form/div/div[3]/button')
					setLogin.click()
					login = True
					setLog("Iniciando Sesion..")


				except NoSuchElementException:
					setLog("Esperando formulario de inicio de sesion..")
					login = False

			ready = False
			while ready == False:
				try:
					avatar = app.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/nav/div/div[3]/div[6]/div/div/div/div/button/div/figure')
					ready = True
					setLog("Mostrando pantalla de bienvenida..")
				except NoSuchElementException:
					ready = False
					setLog("Esperando que manualmente se inicie sesion..")

				time.sleep(data['config']['delays']['delay_general'])

			setScrolls()
			setChannels(app)
		else:
			setScrolls()
			setChannels(app)


		setLog("Refrescando la Pagina")
		app.refresh()
	except WebDriverException:
		
		setLog("Se detecto un cierre de ventana..")
		session_id = ''