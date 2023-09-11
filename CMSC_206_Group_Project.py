
#Alex Levy

#Required Installs:
#tkinter (tk), wikipedia, matplotlib, yfinance, seaborn

#Required Install Commands:
#pip install tk
#pip install wikipedia
#pip install matplotlib
#pip install yfinance

#Dependent on:
#'congress-trading-all.csv' begin in same directory as __main__ - Does not pull live data.

from tkinter import ttk #For more complex gui layouts
from datetime import datetime, timezone #Native (used for date calculations and for plotting)
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg #Allows the use of the canvas widget (embedding plots into tkinter)
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk #Creates a toolbar widget for the data plot

import tkinter as tk #For basic gui functionality
import yfinance #For pulling financial data from yahoo finance
import math #For the floor function
import matplotlib.pyplot as plt #For graphing financial data
import matplotlib.dates as mdates #For changing axis labels for easy comprehension
import matplotlib.animation as ani
import wikipedia #For creating the summary
import pandas as pd #For additional datetime processing

#Creates the additional information output
class summaryFrame(ttk.LabelFrame):
	def __init__(self, container, tickerData, tickerLongName, poliName, stockHistoryData, stockHistoryDates):
		super().__init__(container)

		#Set Frame Label:
		self['text'] = "Data Summary" #Creates the frame label
		self['labelanchor'] = 'nw' #Places the frame label at the top of the frame

		dateOfPurchase = datetime.fromisoformat(f'{tickerData[0]} 00:00:00-04:00') #Converts the date of purchase to a datetime object

		ticker = tickerData[1] #Pulls the ticker name
		
		timeDeltDays = (datetime.today().replace(tzinfo=timezone.utc)-dateOfPurchase).days #This is the number of days since the stock was purchased by the politician

		try:
			dateOfPurchaseReadable = '{:%B %d, %Y}'.format(dateOfPurchase) #Uses f=string formatting to pull a readable format from the datetime
		except Exception as exception:
			print(exception)

		minimumPurchasePrice = int(tickerData[-1])-1 #This is the minimum purchase price as reported in the csv
		minimumPurchasePriceReadable = ('{:,}'.format(minimumPurchasePrice)) #f-string formatting to add commas to the number

		try:
			#get wikipedia summary
			summary = wikipedia.summary(tickerLongName, sentences=2)

			#Create the summary label
			self.wikiSummary = ttk.Label(self, text=f"Stock Summary:\n\t{summary}", wraplength=750, justify="left").grid(column=0, row=1)

		except Exception as exception:
			print(exception)

		self.purchaseSummary = ttk.Label(self, text=f"\nPurchase Summary:\n\t{ticker} was purchased by Congressman {poliName} on {dateOfPurchaseReadable} ({timeDeltDays} days ago) for at least ${minimumPurchasePriceReadable}", justify="left", wraplength=750).grid(column=0, row=2)

		dateOfPurchase = dateOfPurchase.replace(tzinfo = None) #Removes timezone info from the date of purchase (datetime)
		dateOfPurchase = dateOfPurchase.replace(hour=4) #Makes the hour 4 (datetime)
		dateOfPurchase = pd.Timestamp(dateOfPurchase) #Converts to TimeStamp object
		
		stockHistoryData.index = stockHistoryData.index.tz_convert(None) #Removes timezone data from the date indices of the historical financial data

		if dateOfPurchase in stockHistoryData.index:
			pass
		else:
			dateOfPurchase = dateOfPurchase.replace(hour=5) #If the date of purchase is not in the index, try adding an hour and checking again

		try:
			priceAtPurchase = stockHistoryData.loc[dateOfPurchase]
		except Exception as exception:
			print(exception)

		try: #See if the price of the stock at the date of purchase can be pulled
			priceToday = stockHistoryData.iloc[-1]
			pricePercentDelta = round((priceToday-priceAtPurchase) / priceAtPurchase * 100, 2)
			valueToday = round(minimumPurchasePrice / priceAtPurchase * priceToday, 2)
			if pricePercentDelta > 0:
				self.timeDeltSummary = ttk.Label(self, text=f"\n\tIf Congressman {poliName} has held this stock since then, it would be worth ${'{:,}'.format(valueToday)}, appreciating {pricePercentDelta}%\n\n", justify="center")
				self.timeDeltSummary.grid(column=0, row=3)
			elif pricePercentDelta < 0:
				self.timeDeltSummary = ttk.Label(self, text=f"\n\tIf Congressman {poliName} has held this stock since then, it would be worth ${'{:,}'.format(valueToday)}, depreciating {-pricePercentDelta}%\n\n", justify="center")
				self.timeDeltSummary.grid(column=0, row=3)
		except Exception as exception:
			print(exception)
		
		
		self.dataSummary = ttk.Label(self, text=f"\nData Summary:").grid(column=0, row=4)
		
		try:
			importantData = (["Earliest Price", f'${round(stockHistoryData.iloc[0], 2)}', stockHistoryDates[0].strftime('%Y-%m-%d')], ["Price at Purchase", f"${round(stockHistoryData.loc[dateOfPurchase], 2)}", dateOfPurchase.strftime('%Y-%m-%d')], ["Last Price", f"${round(stockHistoryData.iloc[-1], 3)}", stockHistoryDates[-1].strftime('%Y-%m-%d')], )
			self.dataTable = self.createTree(importantData)
		except Exception as exception:
			print(exception)

	def createTree(self, importantData):
		columns = ('Title', 'Price', 'Date')
		tree = ttk.Treeview(self, columns=columns, show='headings', height=3)

		#headings
		tree.heading('Title', text='Title')
		tree.heading('Date', text='Date')
		tree.heading('Price', text='Price')

		for dataPoint in importantData:
			tree.insert('', 0, values=dataPoint)

		tree.grid(column=0, row=5)
		return tree

#Creates the graphical output 
class graphFrame(ttk.LabelFrame):
	def __init__(self, container, poliName, tickerData, tickerLongName):
		super().__init__(container)

		#Set Frame Label:
		self['text'] = "Data Graph" #Creates the frame label
		self['labelanchor'] = 'nw' #Places the frame label at the top of the frame

		ticker = tickerData[1] #Stock ticker

		#date = f"2022-{dateOfPurchase[5:7]}-{dateOfPurchase[8:11]}" #Formats date string as readable datetime
		self.stockHistoryData = yfinance.Ticker(ticker).history(period="2y").iloc[:, 3] #Pulls the financial history of the stock, starting from the day of purchase; then, filters the data to only include the price at close
		self.stockHistoryDates = self.stockHistoryData.index #This pulls the row labels (in this case, the dates that the data was reported, so the closing time of each day. These are datetime objects.
				
		#Plot Data
		fig, ax = plt.subplots() #Creates the axes

		#Creates the animation
		artists = [] #The artist iterable is the series of plots that the animation will cycle through
		for i in range(len(self.stockHistoryData)//7): #Adds the plots to the artist iterable
			lastClose = self.stockHistoryData.iloc[(i-1)*7]
			thisClose = self.stockHistoryData.iloc[i*7]
			if lastClose > thisClose:
				newArtist = ax.plot(self.stockHistoryDates[0:i*7], self.stockHistoryData.iloc[0:i*7], color='red') #Plots the data vs. time if there was a loss
			else:
				newArtist = ax.plot(self.stockHistoryDates[0:i*7], self.stockHistoryData.iloc[0:i*7], color='green') #Plots the data vs. time if there was a gain
			artists.append(newArtist)
		animation = ani.ArtistAnimation(fig=fig, artists=artists, interval=50, repeat=False)


		#Formats the graph
		ax.set_ylabel('Closing Price ($)')
		ax.set_xlabel('Date')
		ax.xaxis.set_major_formatter(mdates.DateFormatter('%y-%b-%d')) #Set the formatting of the date labels as 'YYYY-mm' format

		#Embeds the graph into tkinter
		canvas = FigureCanvasTkAgg(fig, master=self) #Creates a canvas widget
		toolbar = NavigationToolbar2Tk(canvas, self).grid(row=3) #Creates the toolbar, places it on the canvas
		canvas.draw() #Shows the canvas


		#Rotates labels 30 degrees:
		for label in ax.get_xticklabels(which='major'):
			label.set(rotation=30, horizontalalignment='right')

		try:
			canvas.get_tk_widget().grid(row=1, column=0, padx=5, pady=5) #Places the canvas on the window frame
		except Exception as exception:
			print(exception)		

		dateOfPurchase = datetime.fromisoformat(f'{tickerData[0]} 00:00:00-04:00') #Converts the date of purchase to a datetime object
		minPurchasePrice = int(tickerData[2])-1 #This is the minimum price that the politician purchased the stock at
		
		plt.axvline(x=dateOfPurchase) #plots a vertical line at the date when the stock was purchased.

		#Show label
		label = ttk.Label(self, text=tickerLongName).grid(row=0, column=0, pady=5) #Creates a label with the name of the business, placing it over the financial data plot
		
		lastToRecentDifference = int(self.stockHistoryData.iloc[0])-int(self.stockHistoryData.iloc[-1])
		ratioToLast = lastToRecentDifference/self.stockHistoryData.iloc[0]
		percentDelt = round(-ratioToLast*100, 2)
		ttk.Label(self, text = f" The price of {ticker} has changed by {percentDelt}% since April of 2021.").grid(column=0, row=4)

#Creates the information display frame
class displayData(ttk.Labelframe): #Displays the financial data
	def __init__(self, container, poliName, tickerData):
		super().__init__(container)

		self.grid(row=0, rowspan=2, columnspan=2, column=1, padx=10, pady=20, sticky='nw') #Places the plot frame to the right of the buttons.

		self['text'] = "Financial Data" #Creates the frame label
		self['labelanchor'] = 'n' #Places the frame label at the top of the frame
		
		ticker = tickerData[1]

		try:
			tickerInfo = yfinance.Ticker(ticker).info #Pulls info from yfinance on the given ticker
			tickerLongName = tickerInfo['longName'] #Saves the name of the business
		except Exception as exception:
			print(exception)
			tickerLongName = ticker #If a name couldn't be found, keeps the name as the name of the ticker

		self.graphFrames = {}
		self.graphFrames[0] = graphFrame(self, poliName, tickerData, tickerLongName)
		self.graphFrames[1] = summaryFrame(self, tickerData, tickerLongName, poliName, self.graphFrames[0].stockHistoryData, self.graphFrames[0].stockHistoryDates)
		self.frameSelected = self.graphFrames[0]
		self.switchFrame(0)

		#Change screen buttons:
		self.buttonFrame = ttk.Frame(self) #These buttons exist in their own frame.
		self.buttonFrame.grid(column=0, row=6) #Place the button frame
		self.emptySpace = ttk.Label(self.buttonFrame, text = '').grid(row=0, column=0) #Creates whitespace for aesthetic
		self.switchLeft = ttk.Button(self.buttonFrame, text='Graph', style='Switcher.TButton', command=lambda frameDirection=0:self.switchFrame(frameDirection)).grid(row=1, column=0) #Left switcher
		self.switchRight = ttk.Button(self.buttonFrame, text='Summary', style='Switcher.TButton', command=lambda frameDirection=1:self.switchFrame(frameDirection)).grid(row=1, column=1) #Right switcher
		
		self.grid_remove() #Initiate frame as invisible

	def switchFrame(self, frameDirection):
		self.frameSelected.grid_remove()
		self.frameSelected = self.graphFrames[frameDirection]
		self.frameSelected.grid(row=1)

#Creates the ticker selection frame
class ConvertedFrame(ttk.LabelFrame): #Displays the stock buttons
	def __init__(self, container, poliName, poliData): #Initializes each converted frame
		super().__init__(container)
		self.grid(row=1, column=0, padx = 5, pady=5, sticky='nw')
		
		self['text'] = "Purchased Stocks"
		self['labelanchor'] = 'nw'
		#labelFrameStyle = ttk.Style(self)

		purchasedStock = [line[1] for line in poliData]
		lengthPurchasedStock = len(purchasedStock)
		self.financialFrames = {}

		#This generates each button, placing them on the screen consecutively.
		for i in range(len(purchasedStock)):
			self.button = ttk.Button(self, text=purchasedStock[i], command=lambda i=i: self.generateStockFrame(container, i, poliName, poliData), style='Ticker.TButton')
			self.button.grid(column=(i if i<10 else i%(10)), row=math.floor(1/10*i), sticky='nw', padx=2, pady=2)

	#Generates the selected frame when called
	def generateStockFrame(self, container, numOfStock, poliName, poliData):
		if numOfStock in list(self.financialFrames.keys()):
			self.printOnClick(numOfStock)
		else:
			self.financialFrames[numOfStock] = displayData(container, poliName, poliData[numOfStock])
			self.printOnClick(numOfStock)
	
	#Raises selected frame when called
	def printOnClick(self, numOfStock):
		global dataFrame
		try:
			dataFrame.grid_remove()
			dataFrame.toggle()
		except:
			pass
		
		dataFrame = self.financialFrames[numOfStock]
		dataFrame.grid()

#Creates the politician selection frame
class ControlFrame(ttk.LabelFrame): #Inherits the LabelFrame class (Contains the politician selection buttons)
	def __init__(self, container): #Initializes ControlFrame
		super().__init__(container) #Sets app as root
		
		#Configure button styling
		self.labelStyles = ttk.Style(self)
		self.labelStyles.theme_use("winnative")
		self.labelStyles.configure('Ticker.TButton', background='blue', foreground='indigo', font=('Segoe UI', 10, 'bold'), relief='raised')
		self.labelStyles.configure('Politician.TButton', background='blue', foreground='indigo', font=('Segoe UI', 11, 'bold'), relief='groove')
		self.labelStyles.configure('Switcher.TButton', background='blue', foreground='indigo', font=('SegoeUI', 10, 'bold'), borderwidth=4, bordercolor='black')
		self.labelStyles.map('TButton', background=[('active', '#3E8E41')])
		self.labelStyles.configure('Treeview', fieldbackground='red', foreground='purple')
		#self.labelStyles.configure('TButton', background='#4CAF50', foreground='white', borderwidth=0, padding=5, relief='raised', font=('Segoe UI', 11))

		#Generates a list of full company names, for each stock (stored as ticker: long name in dict)
		self.poliNames = list(totalPoliData.keys())
		self.frames={}

		for i in range(len(self.poliNames)): #Create buttons
			self.frames[i] = ConvertedFrame(container, self.poliNames[i], totalPoliData[self.poliNames[i]]) #Loads each frame, adding each one as a function call into the dictionary "self.frames"
			self.frames[i].grid_remove()
			ttk.Button(self, text=self.poliNames[i], command=lambda i=i: self.change_frame(i), style='Politician.TButton').grid(column=(i if i<11 else i%11), row=(math.floor(1/11*i)), padx=2, pady=2) #Creates the button with options, *lambda i=i takes current value of i in iteration
		self['text']="Politicians"
		self['labelanchor'] = 'n'

	def change_frame(self, num): #This function prints the frame change, and changes the frame by raising the "Converted Frame" Class (Every frame is loaded, and then the completed frames are raised when the function is called)
		global frame
		try:
			#Removes frame, but keeps grid options.
			frame.grid_remove()
		except:
			pass
		frame = self.frames[num] #Calls the ConvertedFrame class, passing the name of the politician selected
		frame.grid() 

#Sets the opening screen
class WelcomeFrame(ttk.Frame):
	def __init__(self, container):
		super().__init__(container)

		#Styling
		#Format: subStyle.TKStyle
		self.labelStyles = ttk.Style(self)
		self.labelStyles.theme_use("winnative")
		self.labelStyles.configure('Welcome.TButton', background='blue', foreground='indigo', font=('Segoe UI', 9, 'bold'), relief='raised')
		self.labelStyles.configure('TLabel', font=('Segoe UI', 13, 'bold'))
		self.labelStyles.configure('Welcome.TLabel', font=('Segoe UI', 50, 'bold'))
		self.labelStyles.configure('WelcomeLabel.TLabel', font=('Arial', 75, 'bold'))

		#Frame children
		self.labelText = ttk.Label(self, text = "Congress Financial Report", style = 'WelcomeLabel.TLabel').grid(row=0, pady=30, sticky='n')
		self.welcomeText = ttk.Label(self, text="Welcome", style='Welcome.TLabel').grid(row=1, pady=10)
		self.welcomeButton = ttk.Button(self, text="BEGIN", command=lambda x=1: self.Begin(container, x), style='Welcome.TButton').grid(row=2, pady=5)
		
		self.grid(column=1, row=1)

	def Begin(self, container, x):
		if x:
			self.grid_forget()
			ControlFrame(container).grid(column=0, row=0, padx=5, pady=5, sticky='nw') 

#Creates the display window
class App(tk.Tk):
	def __init__(self):
		super().__init__()

		#Configure window options
		self.title("Politician Selector")
		self.geometry("2000x1000")
		self.resizable(True, True)

		#Configure the grid (weight=width)
		self.columnconfigure(0, weight=0)
		self.columnconfigure(1, weight=1)
		self.rowconfigure(1, weight=1)
		self.rowconfigure(0, weight=0)

#Processes the csv file into a list
def fileProcessing(URL):
	data = [line[0:7] for line in [line.split(",") for line in open(URL, 'r')] if (line[1].startswith("2022") and line[4] == "Purchase")]
	representatives = []
	totalPoliData = {}
	for line in data:
		name = line[3].split(" ")

		#Adjust for named shares (e.g. DUK$A --> DUK, BRK.B -->: BRK-B)
		if "$" in line[2]:
		    line[2] = line[2][0:line[2].find("$")]
		if "." in line[2]:
			loc = line[2].find(".")
			line[2] = list(line[2])
			line[2][loc] = "-"
			line[2] = "".join(line[2])

		#This accomodates for the fact that some representatives have Jr. or II as the name in the last index position.
		if name not in representatives:
			representatives.append(name)
			if len(name[-1]) < 3:
				totalPoliData[name[-2]] = [(line[1], line[2], line[5])] #Appends tuple into the dict, as [(Date, Ticker, Price)]
			else:
				totalPoliData[name[-1]] = [(line[1], line[2], line[5])] #Appends tuple into the dict, as [(Date, Ticker, Price)]
		else:
			if len(name[-1]) < 3:
				totalPoliData[name[-2]].append((line[1], line[2], line[5]))  #Appends tuple into the dict, as [(Date, Ticker, Price)]
			else:
				totalPoliData[name[-1]].append((line[1], line[2], line[5]))  #Appends tuple into the dict, as [(Date, Ticker, Price)]
	return data, representatives, totalPoliData 

#Initiates the program
if __name__ == "__main__":
	data, representatives, totalPoliData = fileProcessing("congress-trading-all.csv")
	app = App()
	WelcomeFrame(app)
	app.mainloop() 