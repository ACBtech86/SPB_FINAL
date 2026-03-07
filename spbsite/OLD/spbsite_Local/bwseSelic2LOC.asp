<% Response.ContentType = "text/xml" %>
<!-- #INCLUDE file="connect.asp" -->
<!-- #INCLUDE FILE="inc/xmlutilbc.asp" -->

<%
  	Dim objXMLx
  	Dim oXslDoc
  	Dim Cabec
  	Dim xslpgm
  	Dim xslapp
	Dim Tabela
	
	xslapp = "bwseREM2LOC"
	xslpgm = xslapp & ".xsl"
	Cabec = "Mensagens Recebidas do Selic"
	Tabela = "SPB_SELIC_TO_LOCAL"
		
	set oXslDoc = getXMLDoc(xslpgm)
 
   	Set objXMLx = RecordsetToXMLDoc(GetRecordset(Tabela), Cabec, xslapp)

 	objXMLx.transformNode oXslDoc
 	
 	Response.Write(objXMLx.xml)

%>

<% 
Function GetRecordset(Tabela)
	Dim cnn
    Dim query
    
    Set cnn = Server.CreateObject("adodb.connection")
    cnn.Open strDBConnection
    query = "select * from " & Tabela
	Set GetRecordset = cnn.Execute(query)

End Function 
%>   

	