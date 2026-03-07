<%
'===================================================================='
' Form Processing subroutines and functions                          '
'===================================================================='
Dim XmlDoc 
Dim SBPFunc 
Dim Pi 
DIM DBConnection      
DIM DBConnection2
DIM ObjNodeRoot
DIM ObjNodebcmsg
DIM ObjNodesismsg
DIM ObjNodemsg
'DIM ObjNodeusermsg
DIM Objcollection 
DIM ObjNodewrk
DIM ObjNodewrk1
DIM strCODGRADE
DIM strISPB
DIM strTBSQLMQ
dim strValor
dim strPrdade
DIM strNUOpe      
DIM strMSGID      
DIM strMSGTAG
DIM strMSGDESCR 
DIM strMSGEMISSOR 
DIM strMSGDEST 
DIM strMSGSEQ 
DIM strMSGCPOTAG
DIM strMSGCPONOME 
DIM strMSGCPOOBRIG 
DIM strMSGCPOTIPO
DIM strMSGCPOTAM 
DIM strMSGCPOFORM 
DIM strMSGIDSelect
DIM DBRS
DIM DBRS2
DIM szSelect
DIM szSeqNuOpe
DIM strWork
DIM strwrktipo
DIM strwrkform
DIM MyPos
DIM strInteiro
DIM StrRest
dim strDataHora
dim nivel 
dim nivelant 
DIM dia      
DIM mes      
DIM ano      
DIM hora      
DIM minuto      
DIM segundo      
DIM rc      
DIM pos      
   
Function MsgFormXml(varFormName,varRequest)

	MsgFormXml = "inprogress"
	redim Objcollection(10)
	Set SBPFunc = Server.CreateObject("SPB.SPBXML")
	SBPFunc.strServer = strServer
	SBPFunc.strDBName = strDBName
	SBPFunc.strUseridServer = strUseridServer
	SBPFunc.strPassWordServer = strPassWordServer
	
	Set XmlDoc = Server.CreateObject("microsoft.xmldom")

    Set DBConnection = Server.CreateObject("adodb.connection")
    DBConnection.Open strDBConnection
    
    Set DBConnection2 = Server.CreateObject("adodb.connection")
    DBConnection2.Open strDBConnection
    strMSGIDSelect = trim(Request.Form("formName"))
    

    szSelect = "SELECT FLD.COD_GRADE, FLD.MSG_ID, FLD.MSG_TAG, FLD.MSG_DESCR, FLD.MSG_EMISSOR , FLD.MSG_DESTINATARIO, FLD.MSG_SEQ, FLD.MSG_CPOTAG, FLD.MSG_CPONOME, FLD.MSG_CPOOBRIG, " & _
               "DIC.MSG_CPOTIPO , DIC.MSG_CPOTAM, DIC.MSG_CPOFORM " & _
               "FROM SPB_MSGFIELD AS FLD  LEFT JOIN SPB_DICIONARIO AS DIC " & _
               "ON FLD.MSG_CPOTAG=DIC.MSG_CPOTAG " & _
               "WHERE FLD.MSG_ID = '" & strMSGIDSelect & "'" & _
               "ORDER BY  FLD.MSG_ID, FLD.MSG_SEQ "

    Set DBRS = Server.CreateObject("adodb.Recordset")
    DBRS.CursorType = 1
    DBRS.LockType = 3
    DBRS.Open szSelect, DBConnection
    Set DBRS2 = Server.CreateObject("adodb.Recordset")
    DBRS2.CursorType = 2
    DBRS2.LockType = 3
	XmlDoc.loadXML ("")
    strValor = "0,00"
    strPrdade = ""
	
    If DBRS.EOF then
        Response.Write("<BR/> Mesagem não encontrada EOF ")
		MsgFormXml = "Erro"
		exit function
	end if
    szSeqNuOpe = SBPFunc.Gera_Num_Ope()
    Response.Write("<BR/> szSeqNuOpe : " & szSeqNuOpe)
    If szSeqNuOpe = "" Then
		MsgFormXml = "Erro"
		exit function
	end IF
    if Not DBRS.EOF then
        If IsNull(DBRS("COD_GRADE")) Then
            strCODGRADE = ""
        Else
            strCODGRADE = Trim(DBRS("COD_GRADE"))
        End If
        Response.Write("<BR/> strCODGRADE : " & strCODGRADE)
	    Select Case strCODGRADE
			Case "SEL01"   
				 strISPB = "00038121" 
				 strTBSQLMQ = "SPB_LOCAL_TO_SELIC"
			Case Else  
				 strISPB = "00038166" 
				 strTBSQLMQ = "SPB_LOCAL_TO_BACEN"
		End Select 
	    DBRS2.Open strTBSQLMQ , DBConnection2,,,2
        If IsNull(DBRS("MSG_TAG")) Then
            strMSGTAG = ""
        Else
            strMSGTAG = Trim(DBRS("MSG_TAG"))
        End If
        If IsNull(DBRS("MSG_EMISSOR")) Then
            strMSGEMISSOR = ""
        Else
            strMSGEMISSOR = Trim(DBRS("MSG_EMISSOR"))
        End If
'		Set Pi = XmlDoc.createProcessingInstruction("xml","version=""1.0""")
'		set ObjNodewrk = AddDoctype(XmlDoc,"SPBDOC","SPBDOC.DTD")
		Set ObjNodeRoot = AddXmlNode(XmlDoc, XmlDoc, "SPBDOC", "")
		Set ObjNodebcmsg = AddXmlNode(XmlDoc, ObjNodeRoot, "BCMSG", "")
		Set ObjNodesismsg = AddXmlNode(XmlDoc, ObjNodeRoot, "SISMSG", "")
'		Set ObjNodeusermsg = AddXmlNode(XmlDoc, ObjNodeRoot, "USERMSG", "")
		Set ObjNodewrk = AddXmlNode(XmlDoc, ObjNodebcmsg, "Grupo_EmissorMsg", "")
		Set ObjNodewrk1 = AddXmlNode(XmlDoc, ObjNodewrk, "TipoId_Emissor", "P")
		Set ObjNodewrk1 = AddXmlNode(XmlDoc, ObjNodewrk, "Id_Emissor", "61377677")
		Set ObjNodewrk = AddXmlNode(XmlDoc, ObjNodebcmsg, "DestinatarioMsg", "")
		Set ObjNodewrk1 = AddXmlNode(XmlDoc, ObjNodewrk, "TipoId_Destinatario", "P")
		Set ObjNodewrk1 = AddXmlNode(XmlDoc, ObjNodewrk, "Id_Destinatario", strISPB)
		Set ObjNodewrk1 = AddXmlNode(XmlDoc, ObjNodebcmsg, "NUOp", szSeqNuOpe)
    end if
	nivel = 0
    Do While Not DBRS.EOF
        strMSGID = Trim(DBRS("MSG_ID"))
        If IsNull(DBRS("COD_GRADE")) Then
            strCODGRADE = ""
        Else
            strCODGRADE = Trim(DBRS("COD_GRADE"))
        End If
        If IsNull(DBRS("MSG_TAG")) Then
            strMSGTAG = ""
        Else
            strMSGTAG = Trim(DBRS("MSG_TAG"))
        End If
        If IsNull(DBRS("MSG_DESCR")) Then
            strMSGDESCR = ""
        Else
            strMSGDESCR = Trim(DBRS("MSG_DESCR"))
        End If
         If IsNull(DBRS("MSG_EMISSOR")) Then
            strMSGEMISSOR = ""
        Else
            strMSGEMISSOR = Trim(DBRS("MSG_EMISSOR"))
        End If
        If IsNull(DBRS("MSG_DESTINATARIO")) Then
            strMSGDEST = ""
        Else
            strMSGDEST = Trim(DBRS("MSG_DESTINATARIO"))
        End If
        If IsNull(DBRS("MSG_SEQ")) Then
            strMSGSEQ = ""
        Else
            strMSGSEQ = Trim(DBRS("MSG_SEQ"))
        End If
        If IsNull(DBRS("MSG_CPOTAG")) Then
            strMSGCPOTAG = ""
        Else
            strMSGCPOTAG = Trim(DBRS("MSG_CPOTAG"))
        End If
        If IsNull(DBRS("MSG_CPONOME")) Then
            strMSGCPONOME = ""
        Else
            strMSGCPONOME = Trim(DBRS("MSG_CPONOME"))
       End If
        If IsNull(DBRS("MSG_CPOOBRIG")) Then
            strMSGCPOOBRIG = ""
        Else
            strMSGCPOOBRIG = Trim(DBRS("MSG_CPOOBRIG"))
        End If
        If IsNull(DBRS("MSG_CPOTIPO")) Then
			strMSGCPOTIPO = ""
            if mid(strMSGCPOTAG,1,6) = "Grupo_" then
				strMSGCPOTIPO = "grupo"
			end if
			if mid(strMSGCPOTAG,1,6) = "Repet_" then
				strMSGCPOTIPO = "repetição"
			end if
            if mid(strMSGCPOTAG,1,7) = "/Grupo_" then
				strMSGCPOTIPO = ""
			end if
			if mid(strMSGCPOTAG,1,7) = "/Repet_" then
				strMSGCPOTIPO = ""
			end if
       Else
           strMSGCPOTIPO = Trim(DBRS("MSG_CPOTIPO"))
       End If
       If IsNull(DBRS("MSG_CPOTAM")) Then
           strMSGCPOTAM = ""
       Else
           strMSGCPOTAM = Trim(DBRS("MSG_CPOTAM"))
       End If
       If IsNull(DBRS("MSG_CPOFORM")) Then
           strMSGCPOFORM = ""
       Else
           strMSGCPOFORM = Trim(DBRS("MSG_CPOFORM"))
       End If
	   strwrktipo = lcase(Trim(strMSGCPOTIPO))
	   strWork = Request.Form(strMSGCPOTAG)
	   Select Case strwrktipo
			Case ""
				if mid(strMSGCPOTAG,1,1) = "/" then    
					nivel = nivel - 1
				else    
					Set Objcollection(0) = AddXmlNode(XmlDoc, ObjNodesismsg, strMSGCPOTAG, "")
				end if	
				strMSGCPOTIPO = ""
			Case "alfanumérico"   
				strMSGCPOTIPO = strwrktipo 
			Case "numérico"   
				strMSGCPOTIPO = strwrktipo 
			Case "grupo"   
				nivelant = nivel 
				nivel = nivel + 1
			    Set Objcollection(nivel) = AddXmlNode(XmlDoc, Objcollection(nivelant), strMSGCPOTAG, "")
				strMSGCPOTIPO = ""
			Case "repetição"   
				nivelant = nivel 
				nivel = nivel + 1
			    Set Objcollection(nivel) = AddXmlNode(XmlDoc, Objcollection(nivelant), strMSGCPOTAG, "")
				strMSGCPOTIPO = ""
			Case Else  
				strMSGCPOTIPO = "hidden"
		End Select 
	    strwrkform = lcase(Trim(strMSGCPOFORM))
	    Select Case strwrkform
			Case "data"   
				pos = Len(strWork)
				if pos < 10 then
				   Response.Write("<BR/> data Invalida : " & strWork)
				   exit function
				end if
				strWork = replace(strWork,"/","")
				dia = mid(strWork,1,2) 
				mes = mid(strWork,3,2) 
				ano = mid(strWork,5,4) 
'				if day(cdate(strWork)) < 10 then
'					dia = "0" & day(cdate(strWork)) 
'				else
'					dia = day(cdate(strWork))
'				end if
'				if month(cdate(strWork)) < 10 then
'					mes = "0" & month(cdate(strWork)) 
'				else
'					mes = month(cdate(strWork))
'				end if
'				ano = year(cdate(strWork))
				strWork = ano&mes&dia
				strMSGCPOTIPO = strwrktipo 
			Case "data hora"   
				pos = Len(strWork)
				if pos < 14 then
				   Response.Write("<BR/> data hora Invalida : " & strWork)
				   exit function
				end if
				strWork = replace(strWork," ","")
				strWork = replace(strWork,"/","")
				strWork = replace(strWork,":","")
				dia = mid(strWork,1,2) 
				mes = mid(strWork,3,2) 
				ano = mid(strWork,5,4) 
				hora = mid(strWork,9,2) 
				minuto = mid(strWork,11,2) 
				segundo = mid(strWork,13,2) 
'				if day(cdate(strWork)) < 10 then
'					dia = "0" & day(cdate(strWork)) 
'				else
'					dia = day(cdate(strWork))
'				end if
'				if month(cdate(strWork)) < 10 then
'					mes = "0" & month(cdate(strWork)) 
'				else
'					mes = month(cdate(strWork))
'				end if
'				ano = year(cdate(strWork))
'				if hour(cdate(strWork)) < 10 then
'					hora = "0" & hour(cdate(strWork)) 
'				else
'					hora = hour(cdate(strWork))
'				end if
'				if minute(cdate(strWork)) < 10 then
'					minuto = "0" & minute(cdate(strWork)) 
'				else
'					minuto = minute(cdate(strWork))
'				end if
'				if second(cdate(strWork)) < 10 then
'					segundo = "0" & second(cdate(strWork)) 
'				else
'					segundo = second(cdate(strWork))
'				end if
				strWork = ano&mes&dia&hora&minuto&segundo
				strMSGCPOTIPO = strwrktipo 
			Case "hora"   
				pos = Len(strWork)
				if pos < 6 then
				   Response.Write("<BR/> hora Invalida : " & strWork)
				   exit function
				end if
				strWork = replace(strWork,":","")
				hora = mid(strWork,1,2) 
				minuto = mid(strWork,3,2) 
				segundo = mid(strWork,5,2) 
'				datawrk = cdate(strWork)
'				if hour(cdate(strWork)) < 10 then
'					hora = "0" & hour(cdate(strWork)) 
'				else
'					hora = hour(cdate(strWork))
'				end if
'				if minute(cdate(strWork)) < 10 then
'					minuto = "0" & minute(cdate(strWork)) 
'				else
'					minuto = minute(cdate(strWork))
'				end if
'				if second(cdate(strWork)) < 10 then
'					segundo = "0" & second(cdate(strWork)) 
'				else
'					segundo = second(cdate(strWork))
'				end if
				strWork = hora&minuto&segundo
				strMSGCPOTIPO = strwrktipo 
		End Select 

'       Response.Write("<BR/> strWork : " & strWork)
'       Response.Write("<BR/> strMSGCPOTAG : " & strMSGCPOTAG)
'       Response.Write("<BR/> strwrktipo : " & strMSGCPOTIPO)
'       Response.Write("<BR/> strMSGCPOFORM : " & strMSGCPOFORM)
'       Response.Write("<BR/> strMSGCPONOME : " & strMSGCPONOME)
'		Response.Write("<BR/> strMSGCPOTIPO: " & strMSGCPOTIPO)
		if strMSGCPOTIPO <> "" then
		    Set ObjNodewrk1 = AddXmlNode(XmlDoc, Objcollection(nivel), strMSGCPOTAG, strWork)
		end if
		if strMSGCPOTAG = "VlrLanc" then
		    strValor = strWork
		end if
		if strMSGCPOTAG = "NivelPref" then
		    strPrdade = strWork
		end if
'       Response.Write("<BR/> MsgFormXml strWork: " & strWork)
        DBRS.MoveNext
    Loop

    
'    XmlDoc.Save ("C:\" & strMSGIDSelect & ".XML")
    DBRS2.AddNew
'	DBRS2("Valor") = strValor
'	DBRS2("Mensagem") = strMSGID 
'	DBRS2("Status") = "P"
'	DBRS2("Tipo") = mid(strMSGID,1,3)
'	DBRS2("Contraparte") = "00038166001098"
'	DBRS2("MsgXml") = 	"<?xml version=""1.0""?>" & _
'		"<!DOCTYPE SPBDOC SYSTEM ""SPBDOC.DTD"">" & XmlDoc.XML
'	DBRS2("Data") = now()
'	DBRS2("Prdade") = strPrdade
	
'	If FlagCidade = 1 then
		DBRS2("NU_OPE") = szSeqNuOpe
		DBRS2("COD_MSG") = strMSGID
		DBRS2("DB_DATETIME") = now()
		DBRS2("MSG") = 	"<?xml version=""1.0""?>" & _
		"<!DOCTYPE SPBDOC SYSTEM ""SPBDOC.DTD"">" & XmlDoc.XML
		DBRS2("STATUS_MSG") = "P"
		DBRS2("FLAG_PROC") = "N"
		if Instr(1,strMSGID,"R1") > 0 then
			DBRS2("MQ_QN_DESTINO") = "QR.RSP.61377677." & strISPB & ".01"
		elseif Instr(1,strMSGID,"R2") > 0 then
			DBRS2("MQ_QN_DESTINO") = "QR.RSP.61377677." & strISPB & ".01"
		else
			DBRS2("MQ_QN_DESTINO") = "QR.REQ.61377677." & strISPB & ".01"
		end if
        Response.Write("<BR/> Tabela Sql : " & strTBSQLMQ)
        Response.Write("<BR/> Queue Destino : " & DBRS2("MQ_QN_DESTINO"))

'	else
'		DBRS2("NU_OPE") = "SYSBACENNNNNNNNN9999999"
'		DBRS2("COD_MSG") = strMSGID
'		DBRS2("DB_DATETIME") = now()
'		DBRS2("MSG") = "<?xml version=""1.0""?>" & _
'		"<!DOCTYPE SPBDOC SYSTEM ""SPBDOC.DTD"">" & XmlDoc.XML
'		DBRS2("STATUS_MSG") = "P"
'		DBRS2("FLAG_PROC") = "N"
'		if Instr(1,strMSGID,"R1") > 0 then
'			DBRS2("MQ_QN_DESTINO") = "QR.RSP.00038166.61377677.01"
'		else
'			DBRS2("MQ_QN_DESTINO") = "QR.REQ.00038166.61377677.01"
'		end if
'	end if

    DBRS2.Update
    
    DBRS.Close
    DBConnection.Close
    DBRS2.Close
    DBConnection2.Close
	MsgFormXml = "validated"

end function

Function AddXmlNode(DOMXML, Parent, Name, Value)
  Set AddXmlNode = AddXmlNodeEx(DOMXML, Parent, Name, Value, "")
End Function

Function AddXmlNodeEx(DOMXML, Parent, Name, Value, Namespace)
  Dim ObjNode
  Set ObjNode = DOMXML.createNode(1, Name, Namespace)
  If Len(Value) <> 0 Then
    ObjNode.Text = Value
  End If
  Parent.appendChild ObjNode
  Set AddXmlNodeEx = ObjNode
  
End Function

'Function AddDoctype(DOMXML, Name, Value)
'  Dim ObjNode
'  Set ObjNode = DOMXML.createNode(10, Name, "")
'  Set AddXmlNodeEx = ObjNode
'End Function

%>