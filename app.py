#importing libraries
import logging
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
import re
import pandas as pd
import time
from functools import reduce
from selenium.webdriver.common.keys import Keys

#logger object  
logger = logging.getLogger("EMA_Hiring")
logger.setLevel(logging.INFO)

# create a file handler
handler = logging.FileHandler('../EMA Test/logs/ema_scrapping.log')
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handler to the logger
logger.addHandler(handler)

def processRawData(element_text):
    #splitting table data into columns and its values
    raw_text = re.split("(?<= -)\n(?=\d)",element_text)
            
    '''scraping columns from raw text data'''
    columns_data_raw = re.split("(?<= -) (?=\w)",raw_text[0])
    
    #splitting first three columns
    columns_data = [columns_data_raw[0][:10], columns_data_raw[0][11:20], columns_data_raw[0][21:]]
    columns_data_raw.pop(0)

    #final columns list
    columns_data.extend(columns_data_raw)
            
    #converting raw_data into tables
    processed_table = pd.DataFrame(data = [i.split(" ") for i in raw_text[1].split("\n")], columns = columns_data,index=None)
    
    return processed_table

def table_traversing(move_cursor, driver, drag, scrap_table_list, flag):
    if flag == False:
        return scrap_table_list
    else:
        move_cursor.click_and_hold(drag).move_by_offset(50, 0).perform()
        time.sleep(10)
        element_text = driver.find_element_by_xpath('//*[@id="pxHandsOn"]/div[1]/div[1]/div[1]/table/tbody').text
        
        table_dataframe = processRawData(element_text)
        if len(scrap_table_list)!=0 and scrap_table_list[-1].equals(table_dataframe):
            flag=False
        else:
            scrap_table_list.append(table_dataframe)
        return table_traversing(move_cursor, driver, drag, scrap_table_list, flag)

def scrap():
    ''' This Function will scrap the data present in below link:
        http://schedule.erldc.in/Report/PXIndex
    '''
    
    try:
        
        vertical_flag = True
        raw_table_list = []
        while vertical_flag:
            
            driver = webdriver.Chrome(executable_path = 'chromedriver.exe')
            driver.get("https://schedule.erldc.in/Report/PXIndex")
            driver.switch_to_frame(0)
            driver.switch_to_active_element()
            #driver.fullscreen_window()
            time.sleep(10)
            
            element_text = driver.find_element_by_xpath('//*[@id="pxHandsOn"]/div[1]/div[1]/div[1]/table/tbody').text
            ini_table_dataframe = processRawData(element_text)
            
            #slide vertical bar
            vertical_drag =  driver.find_element_by_xpath('//*[@id="pxHandsOn"]/div[1]/div[2]/div')
            
            #slide horizontal bar
            horizontal_drag =  driver.find_element_by_xpath('//*[@id="pxHandsOn"]/div[1]/div[3]/div')
            
            move_cursor = ActionChains(driver)
            time.sleep(10)
            move_cursor.click_and_hold(vertical_drag).move_by_offset(0,10).release().perform()
            #storing the scrap table list
            scrap_table_list = [ini_table_dataframe]
            time.sleep(10)
            move_cursor.click_and_hold(horizontal_drag).move_by_offset(10,0).release().perform()
            
            '''horizontal traversing'''
            # data_list object to store tables and its horizontal offset value
            data_list = table_traversing(move_cursor, driver, horizontal_drag, scrap_table_list, flag)
            
            #use built-in python reduce
            table_data_temp = reduce(lambda left,right: pd.merge(left,right[right.columns.difference(left.columns[2:])],on=['Time Block','Time Desc']), data_list)
            raw_table_list.append(table_data_temp)
            driver.close()
            
            if raw_table_list[-1] is not None and raw_table_list[-1].equals(table_data_temp):
                print("Equal")
                vertical_flag = False
            print(table_data_temp.columns,table_data_temp.shape)
    except Exception as e:
        logger.error(exec=True)
        return "Error"

if __name__ == '__main__':
   scrap()            