<%
DIM strServer
DIM strDBName
DIM strUseridServer
DIM strPassWordServer
DIM strDBConnection
      
strServer = "SRVCX077"
strDBName = "BCSPBSTR"
strUseridServer = "SA"
strPassWordServer = "SQLADM"
strDBConnection =  "Provider=SQLOLEDB;Initial Catalog=" & strDBName & ";Data Source=" & strServer & ";uid=" & strUseridServer & ";pwd=" & strPassWordServer
%>