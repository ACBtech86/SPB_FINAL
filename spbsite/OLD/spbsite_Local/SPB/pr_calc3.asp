<%@ Language=VBScript %>
<!-- #INCLUDE file="connect.asp" -->
<%
  Dim objConnection ' As Object
  Dim FilaRS 		' As Object
  Dim CamaraRS 		' As Object
  Dim strSQL 		' As String  
  Dim strMsgid		' As String  
  Dim strItem 		' As String 
  Dim strDescr 		' As String
  Dim strMsgXML 	' As String 
  DIM ValFila 		' As Double
  DIM SeqFila 		' As Long
  Dim NumFila 		' As Long
  Dim TotTot  		' As Long
  Set objConnection = CreateObject("adodb.connection")
	  objConnection.Open strDBConnection
      strSQL = "SELECT Fila.Seq, Fila.Valor, Fila.Mensagem, SPB_MENSAGEM.MSG_DESCR AS Descr, Fila.Status," 
	  strSQL=strSQL & "Fila.Tipo, Fila.Contraparte, Fila.Data, Fila.Prdade, Fila.MsgXml" 
	  strSQL = strSQL & " FROM Fila INNER JOIN SPB_MENSAGEM ON Fila.Mensagem = SPB_MENSAGEM.MSG_ID order by Fila.Data"  
      Set FilaRS = objConnection.Execute(strSQL)
	  strSQL = "SELECT * FROM Camaras "
	  Set CamarasRS = objConnection.Execute(strSQL)
	  TotTot= CamarasRS("TotSTR")+CamarasRS("TotCOMPE")+CamarasRS("TotCIP")
	  Valfila= 0
	  NumFila= 0
%>  
<script LANGUAGE="javascript">
function Mascara(Valor)
{ var cont,mascarado,cont2;
 cont = 0;
 mascarado = "";
 var Size = Valor.length;
 while(Size!=0)
 {   mascarado = Valor.substring(Size - 1, Size) + mascarado;
     cont++;
     if(cont > 2)
     {  cont2++;
        if((cont2 == 3) && (Size != 1))
        { mascarado = "." + mascarado
          cont2 = 0; }
     }
     if(cont == 2)
     { mascarado = "," + mascarado;
     cont2=0;} 
 Size--;
 }
 return mascarado;
}//fim funcao
function UnMask(Valor)
{ var cont,mascarado,cont2;
 cont = 0;
 mascarado = "";
 var Size = Valor.length;
 while(Size!=0)
 {   mascarado = Valor.substring(Size - 1, Size) + mascarado;
     cont++;
     if(cont > 2)
     {  cont2++;
        if((cont2 == 3) && (Size != 1))
        {  cont2 = 0;
           Size--;   }
     }
     if(cont == 2)
     {  Size--;
        cont2=0; } 
 Size--; 
 }
 return mascarado;
}//fim funcao
function Processa(receb)
{
var NVS = new String(receb).split("|");
alert(NVS);
 if(NVS[2]=="true")
 {document.calc.qtdnsel.value = parseInt(document.calc.qtdnsel.value) - 1;
 document.calc.valnsel.value = Mascara(new String( (parseFloat(UnMask(document.calc.valnsel.value)) - parseFloat(UnMask(NVS[1])))));
 document.calc.qtdsel.value = parseInt(document.calc.qtdsel.value) + 1;
 document.calc.valsel.value = Mascara(new String( (parseFloat(UnMask(document.calc.valsel.value)) + parseFloat(UnMask(NVS[1])))));
 document.calc.processados.value = document.calc.processados.value + "|" + NVS[0]; }
 else
 { document.calc.qtdnsel.value = parseInt(document.calc.qtdnsel.value) + 1;
   document.calc.valnsel.value = Mascara(new String( (parseFloat(UnMask(document.calc.valnsel.value)) + parseFloat( UnMask(NVS[1] )))));
   document.calc.qtdsel.value = parseInt(document.calc.qtdsel.value) - 1;
   document.calc.valsel.value = Mascara(new String((parseFloat( UnMask(document.calc.valsel.value)) - parseFloat(UnMask(NVS[1])))));
RemoveFila(NVS[0]);}
}
function RemoveFila(receb)
{
var Ajustar = document.calc.processados.value;
var Organizar = new String(Ajustar).split("|");
 for (i=0;i<Organizar.length;i++)
 { if(Organizar[i] == receb) { Organizar[i] = "d"; }}//fim for
 Organizar.join;
 document.calc.processados.value = Organizar;
}//fim funcao

function Mostra (theXML)
{	var teste1;
	palette = window.open("","paletteWindow","toolbar=no,location=no, menubar=no,scrollbars=yes,resizable=no,width=400,height=300,screenX=100, screenY=100,alwaysRaised");
	palette.location.href="mostra.asp?qual=" + theXML
}
</script>
<html>
<head>
<meta http-equiv="Expires" content="0">
<meta http-equiv="Last-Modified" content="0">
<meta http-equiv="Cache-Control" content="no-cache, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
	<title>Sistema de Pagamento Brasileiro.</title>
</head>
<link rel="stylesheet" href="cidadespb.css">
<body marginheight="0" topmargin=10 bottommargin="0" leftmargin=0 rightmargin="0">


<table width="716" height="20" border="0" cellspacing="0" cellpadding="0" align="center">
  <tr> 
    <td width="200" height="60" valign="top" background="logocp1.gif"></td>
    <td background="tit_back.gif" height="20" valign="middle" colspan="2"> 
      <div align="right"><font face="Verdana, Arial, Helvetica, sans-serif" size="+2"><b><i><font color="#FFFFFF">cidadeSPB</font></i></b></font></div>
    </td>
  </tr>
</table>
<table width="700" border="0" cellspacing="0" cellpadding="0" align="center">
  <tr NOWRAP align="left" valign="middle"> 
	    <td class="HMenu" height="15" colspan="3">&nbsp;
<a  class="HMenu" title="Vamos ver">Piloto STR&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
</a>|<a class="HMenu">Historico de Mensagens&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
</a>|<a class="HMenu">Erros em mensagens&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
</a>|<a class="HMenu">Configuração&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
</a>|<a class="HMenu">Selic&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</a> 
|<a class="HMenu" href="inic.htm">Mensagens STR&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</a> 

	   </td>
	  </tr>
<tr><td width="680">
<div id="alvo" style="overflow-y:scroll; width:680px; height:230px; z-index:0; left: auto; top: 75px">
<table align= "center" cellpadding="1" cellspacing="1" border="0" width="700">
<tr>
	<td><form method="post" action="" name="piloto">
		<table cellpadding="2" cellspacing="1" border="0" width="100%">
			<tr >
				<td  width="15"></td>
				<td >Mensagem</td>
				<td align= "right">Valor</td>
				<td>Situação</td>
				<td>Origem</td>
				<td width="70">Contra-Parte</td>
				<td>Data</td>
				<td>Pr.</td>
			</tr>
<%
      While NOT FilaRS.EOF
	  NumFila = NumFila + 1
	  SeqFila = FilaRS("Seq")
	  strDescr = FilaRS("Descr")
	  ValFila = Valfila + FilaRS("Valor") 
%>
				<tr>
				<td width="15"><input type="Checkbox" id="msg<%= SeqFila %>" name="msg<%= SeqFila %>" value="msg<%= SeqFila %>|<%= formatnumber(FilaRS("Valor"),2) %>"  onclick="javascript:Processa(document.piloto.msg<%= SeqFila %>.value + '|' + document.piloto.msg<%= SeqFila %>.status)"></td>
				<td><a href="javascript:Mostra( <%= SeqFila %>)" title ="<%= strDescr  %>"  class="vermelho"><%= FilaRS("Mensagem") %></a></td>
				<td align= "right"><%= formatnumber(FilaRS("Valor"),2) %></td>
				<td><%= FilaRS("Status") %></td>
				<td><%= FilaRS("Tipo") %></td>
				<td width="70"><%= FilaRS("Contraparte") %></td>
				<td><%= FilaRS("Data") %></td>
				<td><%= FilaRS("Prdade") %></td>
			</tr> 
<% 
        FilaRS.moveNext
      Wend
%>  
		</table>
	</form></td>
</tr>
</table>
</div>
  <table  width="716" border="0" cellspacing="1" cellpadding="0" align="center" bgcolor="Black">
	<tr>
		<td width="350" valign="top">
		<form method="post" action="Atualiza.asp" name="calc">
			<table width="300" height="100%" border="0" cellspacing="0" cellpadding="2" align="center">
				<tr >
					
				</tr>
				<tr >
				<td></td>
					<td>Quantidade:</td>
					<td>Valor:</td>
				</tr>
				<tr >
					<td ><b>Fila</b></td>
					<td><input type="Text" name="qtdnsel" size ="6" value ="<%= NumFila %>" ></td>
					<td><input type="Text" name="valnsel" size="14" Value ="<%= formatnumber(ValFila,2) %>" ></td>
				</tr>
				<tr >
				<td width="6">Selecionadas</td>
					<td><input type="Text" name="qtdsel" size= "6" value ="0"></td>
					<td><input type="Text" name="valsel" size="14" value ="0"></td>
				</tr>
				<tr >
					<td colspan="2" align="right"><input type="submit" value="Enviar" ></td>

				</tr>
			</table>
		<input type="hidden" value="" name="processados">
		</form>
		</td>
		<td width="350">
			<table border="0" cellpadding="1" cellspacing="0" width="400">
				<tr >
					<td>Saldo</td>
					<td align="center"><b>STR</b></td>
					<td align="center"><b>Futuro</b></td>
				</tr>
				<tr></tr>
				<tr >
					<td>Selic</td>
					<td align="center"><input type="Text" value="<%= formatnumber(CamarasRS("TotSTR"),2) %>"></td>
					<td align="center"><input type="Text" value="2.128.413,00"></td>
				</tr>
				
				<tr >
					<td>Compe</td>
					<td align="center"><input type="Text" value="<%= formatnumber(CamarasRS("TotCOMPE"),2) %>"></td>
					<td align="center"><input type="Text" value="3.548,00"></td>
				</tr>
				<tr >
					<td>Pg.</td>
					<td align="center"><input type="Text" value="<%= formatnumber(CamarasRS("TotCIP"),2) %>"></td>
					<td align="center"><input type="Text" value="10.762.169,00"></td>
				</tr>
				<tr >
					<td>Geral</td>
					<td align="center"><input type="Text" value="<%= formatnumber(TotTot,2) %>"></td>
					<td align="center"><input type="Text" value="16.993.556,42"></td>
				</tr>
			</table>
		</td>
	</tr>
	<tr bgcolor="e6e6e6">
		<tD colspan="2" align="center" height="30" valign="middle">
			<a href="frm_erromensageria.shtml" target="site" class="vermelho"><b>Status Operacional</b></a>
		</td>
	</tr>
</table>


</table></body>
</html>
	