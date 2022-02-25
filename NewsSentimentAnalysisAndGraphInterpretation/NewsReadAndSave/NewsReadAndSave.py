import pyodbc
import requests
import codecs

# -------------------------------------------------Türkçe Metinlerde Duygu Analizi------------------------------------------------------------------
classification_training=[]
sentences_training=[]

posTxt = codecs.open("pos.txt", "r", "utf-8")


posTxt_content=posTxt.read()

posTxt_contentList = posTxt_content.splitlines()

for i in range(len(posTxt_contentList)):
    classification_training.append(1)
    sentences_training.append(posTxt_contentList[i])

   

posTxt.close()

negTxt = codecs.open("neg.txt", "r", "utf-8")


negTxt_content=negTxt.read()


negTxt_contentList = negTxt_content.splitlines()

for i in range(len(negTxt_contentList)):
    classification_training.append(0)
    sentences_training.append(negTxt_contentList[i])


   
negTxt.close()

from sklearn.feature_extraction.text import TfidfVectorizer 
vectorizer = TfidfVectorizer(analyzer='word', lowercase = True)

sen_train_vector = vectorizer.fit_transform(sentences_training) #cümleleri vektöre çevirdik ki bilgisayar anlasın.

from sklearn.naive_bayes import GaussianNB
clf = GaussianNB()
model = clf.fit(X=sen_train_vector.toarray(), y=classification_training) #modelimizi oluşturduk.


# ------------------------------Haber İnternetten Çekme, Kaydetme Ve Haberlerin Duygu Analizlerinin Yapılması---------------------------------------------------------------------
news_article_title=[]
news_article_desc=[]
news_article_url=[]
news_article_publishedAtinTime=[]
news_article_publishedAt=[]
newsTotalRes=0

def getNews(news_article_desc:list,news_article_title:list):
    api_key="8f95dcb4143247aba4355e22498e0639"
    url="https://newsapi.org/v2/top-headlines?country=tr&apiKey="+api_key
    news=requests.get(url).json()
    newsTotalRes=news["totalResults"]
    article=news["articles"]
        
    for arti in article:
        news_article_title.append(arti['title'])
        news_article_desc.append(arti['description'])
        news_article_url.append(arti['url'])
        news_article_publishedAtinTime.append(arti['publishedAt']) #Burada zamanla beraber çekiyoruz haberi 
      
    
try:
    getNews(news_article_desc,news_article_title)
except:
    print("haberler internetten çekilemedi")
 


for i in range(len(news_article_publishedAtinTime)): #burada sadece tarihleri alıyoruz. saat,dakika, saniye almıyoruz.
    news_article_publishedAt.append(news_article_publishedAtinTime[i][:+10])



try: #db baglantısı
    conn=pyodbc.connect(  
        "Driver={SQL Server Native Client 11.0};"
        "Server=DESKTOP-IK7PVOC;"
        "Database=TextDet_DB;"
        "Trusted_Connection=yes;"
    )
except:
    print("veri tabani ile baglanti kurulamadi")

db_news_article_title=[]
db_news_article_desc=[]
db_news_article_url=[]

def readGazeteHaberleri_Db(conn): #gazete haberleri baslıgını, içeriğini ve url'sini çekiyor.
    cursor=conn.cursor()
    cursor.execute("select * from GazeteHaberleri")
    for row in cursor:
        db_news_article_title.append(row[1])
        db_news_article_desc.append(row[2])
        db_news_article_url.append(row[3])   
        
try:        
    readGazeteHaberleri_Db(conn)   
except:
    print("gazete haberleri veri tabanindan cekilemedi")


db_news_article_publishedAt=[]

def readGazeteHaberleriResult_Db(conn): #db'den gazete haberlerinin tarihlerini çekiyor.
    cursor=conn.cursor()
    cursor.execute("select Tarih from GazeteHaberResult")
    for row in cursor:
        db_news_article_publishedAt.append(row[0])
    
     

try:
    readGazeteHaberleri_Db(conn) 
except:
    print("gazete haberleri tarihleri veri tabanindan cekilemedi")


result_news_article_title=[]
result_news_article_desc=[]
result_news_article_url=[]
result_news_article_publishedAt=[]

bayrak=0

for i in range(len(news_article_url)): #db deki ve yeni haberleri kıyaslıyor, eğer haber db de var ise db ye ekleme yapmıyor haberi.
    bayrak=0
    for j in range(len(db_news_article_url)):
        if(news_article_url[i]==db_news_article_url[j]):
            bayrak=1
    if(bayrak==0):
        result_news_article_title.append(news_article_title[i])
        result_news_article_desc.append(news_article_desc[i])
        result_news_article_url.append(news_article_url[i])
        result_news_article_publishedAt.append(news_article_publishedAt[i])




#db'den silinecek olan şeyler için yapıyoruz bu kısmı.
silinecekuzunluk=len(result_news_article_url)-1
silinecekList=[]

for i in range(len(result_news_article_url)):  #i nin degeri silinecekuzunluk değeri azalsa bile ilk haline göre değer alıyor.
     if((result_news_article_title[i] == None) or (result_news_article_desc[i] == None) or (result_news_article_url[i] == None) or (result_news_article_publishedAt[i]== None)):
        silinecekList.append(i)


bayrak=0
silinensay=0

for element in silinecekList:
    if(bayrak==0):
          result_news_article_title.remove(result_news_article_title[element])
          result_news_article_desc.remove(result_news_article_desc[element])
          result_news_article_url.remove(result_news_article_url[element])
          result_news_article_publishedAt.remove(result_news_article_publishedAt[element])
          bayrak=1
          silinensay=silinensay+1
         
    else:
         element=element-silinensay
         result_news_article_title.remove(result_news_article_title[element])
         result_news_article_desc.remove(result_news_article_desc[element])
         result_news_article_url.remove(result_news_article_url[element])
         result_news_article_publishedAt.remove(result_news_article_publishedAt[element])
         silinensay=silinensay+1
    

result_news_article_Id=[]
get_url=""

def readGazeteHaberleriId_Db(conn): #Gazete haber ıd lerini okumak için veri tabanından çekiyoruz.Bunuda url'i kullanarak yapıyoruz.
    cursor=conn.cursor()
    for i in range(len(result_news_article_url)):
        get_url=result_news_article_url[i]    
        cursor.execute("select Id from GazeteHaberleri where Url='"+get_url+"'; ")
        for row in cursor:
            result_news_article_Id.append(row[0])
    
    result_news_article_url.clear()
    

def insertGazeteHaberleri_db(conn): 
    cursor=conn.cursor()
    for i in range(len(result_news_article_title)):    
        cursor.execute('insert into GazeteHaberleri (Title,Description,Url) values(?,?,?);', 
                   (result_news_article_title[i],result_news_article_desc[i],result_news_article_url[i])
                      )
    conn.commit()
    result_news_article_title.clear()
    result_news_article_desc.clear()
    readGazeteHaberleriId_Db(conn)

result_news_article_desc_sentiment_array=[] 
result_news_article_desc_sentiment_list=[]
result_news_article_desc_sentiment=[]


try: #haberlerin duygu analizi için yaptık.
    if(len(result_news_article_desc)>0):
        sen_test_vector = vectorizer.transform(result_news_article_desc)
        y_pred = model.predict(sen_test_vector.toarray())
        result_news_article_desc_sentiment_array.append(y_pred)

        for i in range(len(result_news_article_desc_sentiment_array[0])):
            result_news_article_desc_sentiment_list.append(result_news_article_desc_sentiment_array[0][i])
    
        for i in range(len(result_news_article_desc_sentiment_list)):
            if(result_news_article_desc_sentiment_list[i]==1):
                result_news_article_desc_sentiment.append("True")
            if(result_news_article_desc_sentiment_list[i]==0):
                result_news_article_desc_sentiment.append("False")
except:
    print("haberlerin duygu analizini yaparken hata olustu")
        

try:
    insertGazeteHaberleri_db(conn) 
except:
    print("veri tabanina gazete haberlerini ekleme esnasinda hata olustu")


def insertGazeteHaberleriResult_db(conn): #burayı düzeltmem gerek: 1-)veri tabanındaki elemanlara göre işlem yapıp eklemeyi öğrenmem lazım, yeni çekilen haberlere göre değil.
    cursor=conn.cursor()
    for i in range(len(result_news_article_Id)):    
        cursor.execute('insert into GazeteHaberResult (GazeteHaber_Id,Tur,Tarih) values(?,?,?);', 
                   (result_news_article_Id[i],result_news_article_desc_sentiment[i],result_news_article_publishedAt[i])
                      )
    conn.commit()
    result_news_article_Id.clear()
    result_news_article_desc_sentiment.clear()
    result_news_article_publishedAt.clear()
try:
    insertGazeteHaberleriResult_db(conn)    
except:
    print("İnternetten Çekilen Haberlerin Duygu Analizlerinin Kaydini yaparken hata olustu")


#--------------------------------------------------------Grafik Eksenlerini Oluşturma--------------------------------------------------------------

db_news_date=[]

def readGazeteHaberleriResult_Tarih_Db(conn):
    cursor=conn.cursor()
    cursor.execute("select Tarih from GazeteHaberResult")
    for row in cursor:
        db_news_date.append(row[0])
    
    
       

try:
    readGazeteHaberleriResult_Tarih_Db(conn)
except:
    print(" Veri tabanindan tarihleri okurken hata olustu")



db_news_result_date=[]
bayrak=0

for i in range(len(db_news_date)):
    bayrak=0
    for j in range(len(db_news_result_date)):
        if(db_news_date[i]==db_news_result_date[j]):
            bayrak=1
    if(bayrak==0):
        db_news_result_date.append(db_news_date[i])


import time
db_news_result_date.sort(key=lambda x: time.mktime(time.strptime(x,"%Y-%m-%d")))


db_news_result_date_typePercent=[]

def readGazeteHaberleriResult_Date_Type_Per_Db(conn): #Tarihe göre olumluluk yüzdesi hesaplama.   
    cursor=conn.cursor()
    for i in range(len(db_news_result_date)):
        db_news_type=[]
        true_count=0
        false_count=0
        totalCount=0
        get_date=db_news_result_date[i]
        cursor.execute("select Tur from GazeteHaberResult where Tarih='"+get_date+"'; ")
        for row in cursor:
            db_news_type.append(row[0])
        for i in range(len(db_news_type)):
            if(db_news_type[i]==0):
                false_count=false_count+1
            if(db_news_type[i]==1):
               true_count=true_count+1
        totalCount=true_count+false_count
        true_percent= (true_count / totalCount) *100  #olumluluk yüzdesini hesaplıyorum.
        db_news_result_date_typePercent.append(round(true_percent,2)) #burada 2 basamagını alıyorum yüzdenin.
        

try:
    readGazeteHaberleriResult_Date_Type_Per_Db(conn)
except:
    print("Gazete haberlerin tarihe gore yuzde tur oranlarını hesaplarken hata olustu.")


#print("x ekseni(Tarihler)")
#print(db_news_result_date)

#print("y ekseni (Olumlu haber yuzdesi haberlerin )")
#print(db_news_result_date_typePercent)


#---------------------------------------Duygu Analizi Grafiğe Dökülmüş Hali-------------------------------------------------------

import matplotlib.pyplot as plt  

try:
    plt.figure()
    plt.plot(db_news_result_date,db_news_result_date_typePercent,"ko--")
    plt.xlabel('Tarihler')
    plt.ylabel('Haber Olumluluk yüzdesi')
    plt.title('Günlük Haber Olumluluk Yüzdesi')
    plt.show()
except:
    print("Grafik cizilemedi")







