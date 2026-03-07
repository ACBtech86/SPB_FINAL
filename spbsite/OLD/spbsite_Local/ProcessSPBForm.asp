<%
'===================================================================='
' Form Processing subroutines and functions                          '
'===================================================================='
Dim intErrorNum   ' As Integer
Dim strFormMode   ' As String
Dim strStatus     ' As String
Dim strFormAction ' As String
Dim strCheckDB    ' As String
Dim objForm       ' As Object
Dim strPath       ' As String
Dim strFormName   ' As String
Dim strFormStyle  ' As String
Dim strFormError  ' As String
Dim objReqForm    ' As String
DIM strXmlDB      ' As String
DIM strXslDB      ' As String
'--------------------------------------------------------------------'
'  Main function that controls the form processing stages            ' 
'--------------------------------------------------------------------'
Function processForm(varFormName,varRequest)

  processForm = "inprogress"

  Set objForm = Server.CreateObject("microsoft.xmldom")
'  Response.Write ("Debug processForm inicio. <BR/>")

  '---- if no formStatus then must be an initial load ----'
  If len(varRequest.Form("formStatus")) = 0 Then
   
  '---- call the function to load the form in the xml object ----'   
'	  Response.Write ("Debug processForm loadform. <BR/>")
     If loadForm(varFormName) Then
   
  '---- if the load was succesful then convert to HTML and display ----'   
' 	   Response.Write ("Debug processForm displayForm strFormStyle. <BR/>")
       Response.Write(displayForm(strFormStyle))
     Else
' 	   Response.Write ("Debug processForm displayForm strFormError. <BR/>")
       Response.Write(displayForm(strFormError))
     End If

  '---- formStatus is present so validate the form ----'
  Else 
  
  '---- if the form is valid take appropriate action ----'
' 	 Response.Write ("Debug processForm validFormr. <BR/>")
     If validForm(varFormName,varRequest) Then
'        call deleteTemp(varFormName,Session.SessionID)
' 		Response.Write ("Debug processForm validated. <BR/>")
        processForm = "validated"

  '---- otherwise re-display the form, including error messages ----'
     Else
' 		Response.Write ("Debug processForm displayForm strFormStyle. <BR/>")
        Response.Write(displayForm(strFormStyle))
     End If
  End If

End Function


'--------------------------------------------------------------------'
' load form into xml form object
'--------------------------------------------------------------------'
Function loadForm(varFormName) 'As Boolean

  loadForm = false

  '---- load the form into the object ----'
' Response.Write ("Debug loadForm inicio. <BR/>")
  loadFileDB(varFormName)
'  Response.Write ("Debug loadFileDB ok. <BR/>")
'  If loadFile(objForm, strPath & "\" & varFormName & ".xml") Then
  If loadFileXml(objForm) then
'     Response.Write ("Debug initFields ini. <BR/>")
     call initFields()
'     Response.Write ("Debug initFields ok. <BR/>")
     call expandLookUps()
     loadForm = true
'     call setStatus("input")
'     objForm.save(strPath & "\" & varFormName & Session.SessionID & ".xml")
  End If
' Response.Write ("Debug loadForm fim. <BR/>")

End Function
    
'--------------------------------------------------------------------'
' validate the form  
'--------------------------------------------------------------------'
Function validForm(varFormName,varRequest) 'As Boolean   
  
  Dim objList ' As Object
  
  intErrorNum = 0 
  Set objReqForm = varRequest.Form
  validForm = true
  
'  If loadFile(objForm, strPath & "\" & varFormName & Session.SessionID & ".xml") Then
'  Response.Write ("Debug validForm loading. <BR/>")
 
  loadFileDB(varFormName)
  
'  If loadFile(objForm, strPath & "\" & varFormName & ".xml") Then
  If loadFileXml(objForm) then
     '---- validate the FIELDSETs ----'
    If validFieldSet(objForm.documentElement) = "VALID ENTRY" Then
'        Response.Write ("Debug validForm true. <BR/>")
        validForm = true        
     Else
'        Response.Write ("Debug validForm false. <BR/>")
        validForm = False
     End If
  else 
     validForm = False
  End If

'  If validForm Then
'     Response.Write ("Debug Status complete. <BR/>")
'     call setStatus("complete")
'  Else
'     Response.Write ("Debug Status error. <BR/>")
'     call setStatus("error")
'  End If
       
End Function


'--------------------------------------------------------------------'
' display the form 
' - use the transform node to convert to HTML 
'--------------------------------------------------------------------'
Function displayForm(varStyleSheet)

  Dim objStyleSheet ' As Object
  
  Set objStyleSheet = Server.CreateObject("microsoft.xmldom")
  
  loadFileDB(varStyleSheet)
'  If loadFile(objStyleSheet, strPath & "\" & varStyleSheet & ".xsl") Then
  If loadFileXsl(objStyleSheet) Then
     displayForm = objForm.transformNode(objStyleSheet.documentElement)
  Else
     displayForm = "Problems loading Stylesheet " & varStyleSheet & "</B>"
  End If

End Function

'--------------------------------------------------------------------'
' Delete the temporary form file
'--------------------------------------------------------------------'
'Sub deleteTemp(varFormName,varSessionID)
'
'  Dim objFSO      'As Object
'  Dim strFileName ' As String
'  
'  Set objFSO  = Server.CreateObject("Scripting.FileSystemObject")
'  
'  strFileName = strPath & "/" & varFormName & varSessionId & ".xml" 
'  
'  If objFSO.FileExists(strFileName) Then 
'     objFSO.DeleteFile(strFileName)
'  End If
'
'End Sub
'--------------------------------------------------------------------'
' validate fieldsets 
'--------------------------------------------------------------------'
Function validFieldSet(varFieldSet) ' As Boolean

  Dim intMin 'As Integer
  Dim intMax 'As Integer
  Dim intEntered 'As Integer
  Dim intChildCount 'As Integer
  Dim intChildSub ' As Integer
  Dim intErrors ' As Integer
  Dim strCriteria ' As String
  Dim strValidResult 'As String

  intMin     = 0
  intMax     = 999
  intEntered = 0
  intErrors  = 0 

  '---- set the min and max ----'
  If varFieldSet.getAttribute("min") >= 0 Then 
     intMin = cint(varFieldSet.getAttribute("min"))
  End If
  If varFieldSet.getAttribute("max") >= 0 Then 
     intMax = cint(varFieldSet.getAttribute("max"))
  End If

  intChildCount = varFieldSet.childNodes.length - 1
  
  For intChildSub = 0 to intChildCount

      Select Case varFieldSet.childNodes.item(intChildSub).nodeName 
         Case "FIELDSET"  
            strValidResult = validFieldSet(varFieldSet.childNodes.item(intChildSub)) 
         Case "FIELD"
            strValidResult = validInput(varFieldSet.childNodes.item(intChildSub)) 
         Case Else
      End Select

      Select Case ucase(strValidResult)
         Case "NO ENTRY"
         Case "VALID ENTRY"
            intEntered = intEntered + 1
         Case "INVALID ENTRY"
            intErrors  = intErrors + 1
         Case Else
      End Select

  Next
  
  '---- get count of error inputs ----'
  If intErrors > 0 Then 
     validFieldSet = "INVALID ENTRY"
  Else
     '---- if option is required or fields entered > 0 then check within limits ----'  
     If varFieldSet.getAttribute("req") = "yes" And _
        intEntered = 0 Then
        writeError varFieldSet,"Details required"
        validFieldSet = "INVALID ENTRY"
     ElseIf(varFieldSet.getAttribute("req") = "yes" And _
        intEntered > 0) Or _
        intEntered > 0  Then 
        If intEntered >= intMin And intEntered <= intMax Then
           varFieldSet.setAttribute "entered","yes"
           validFieldSet = "VALID ENTRY"
        Else
           If intEntered = 0 Then 
              writeError varFieldSet,"Details required"
              validFieldSet = "INVALID ENTRY"
           Else
              writeError varFieldSet,"You have not entered the correct number of details"
              validFieldSet = "INVALID ENTRY"
           End If 
        End If
     Else
        validFieldSet = "NO ENTRY"
     End If
  End If
        
End Function

'--------------------------------------------------------------------'
' 
'--------------------------------------------------------------------'
Function validInput(varInput) 'As String

  Dim objOptionList   ' As Object
  Dim objOption       ' As Object
  Dim strValue        ' As String
  
  strValue   = objReqForm(varInput.getAttribute("name"))
'  Response.Write ("Debug ValidInput strValue: " & strValue & "<BR/>")
  validInput = "VALID ENTRY"
  
  If strValue = "" Then
     If varInput.getAttribute("req") = "yes" Then
        validInput = "INVALID ENTRY"
        writeError varInput, "Campo é obrigatório"
     Else
        validInput = "NO ENTRY"
     End If 
  Else 
     Select Case varInput.getAttribute("type")
       Case "text"
          varInput.setAttribute "value",strValue
          varInput.setAttribute "entered","yes"
       Case "textarea"
          If strValue <> "Enter text" Then 
             varInput.setAttribute "value",strValue
             varInput.setAttribute "entered","yes"
          End If    
       Case "number"
          varInput.setAttribute "value",strValue
          varInput.setAttribute "entered","yes"
          If NOT isNumeric(strValue) Then
             validInput = "INVALID ENTRY"
             writeError varInput, "Este é um numero invalido"
          End If    
       Case "telephone"
          varInput.setAttribute "value",strValue
          varInput.setAttribute "entered","yes"
          If NOT isTelephone(strValue) Then
             validInput = "INVALID ENTRY"
             writeError varInput, "Este é um numero invalido"
          End If    
       Case "date"
          varInput.setAttribute "value",strValue
          varInput.setAttribute "entered","yes"
          If NOT isDate(strValue) Then
             validInput = "INVALID ENTRY"
             writeError varInput, "Esta é uma data invalida"
          End If  
       Case "time"
          varInput.setAttribute "value",strValue
          varInput.setAttribute "entered","yes"
          If NOT isDate(strValue) Then
             validInput = "INVALID ENTRY"
             writeError varInput, "Esta é uma hora invalida"
          End If  
       Case "datetime"
          varInput.setAttribute "value",strValue
          varInput.setAttribute "entered","yes"
          If NOT isDate(strValue) Then
             validInput = "INVALID ENTRY"
             writeError varInput, "Esta é uma data ou hora invalida"
          End If  
       Case "email"
          varInput.setAttribute "value",strValue
          varInput.setAttribute "entered","yes"
          If NOT isEmail(strValue) Then
             validInput = "INVALID ENTRY"
             writeError varInput, "This is an invalid email address"
          End If
       Case "ccard"
          varInput.setAttribute "value",strValue
          varInput.setAttribute "entered","yes"
          If NOT isCCard(strValue) Then
             validInput = "INVALID ENTRY"
             writeError varInput, "This is an invalid credit card number"
          End If
       Case "radio"
          If varInput.getAttribute("value") = strValue Then
             varInput.setAttribute "checked","yes"
             varInput.setAttribute "entered","yes"
          Else
             validInput = "NO ENTRY"
          End If
       Case "checkbox"
          If varInput.getAttribute("value") = strValue Then
             varInput.setAttribute "checked","yes"
             varInput.setAttribute "entered","yes"
          Else
             validInput = "NO ENTRY"
          End If
       Case "select"
          Set objOptionList = varInput.selectNodes("OPTION")
          For each objOption in objOptionList
              If objOption.getAttribute("value") = strValue Then
                 objOption.setAttribute "selected","yes"
                 varInput.setAttribute "entered","yes"
                 varInput.setAttribute "value",strValue
              Else 
                 objOption.setAttribute "selected","no"
              End If
          Next 
       Case Else
    End Select

  End If
  
End Function

'--------------------------------------------------------------------'
' 
'--------------------------------------------------------------------'
Function isTelephone(varNumber)

  Dim strNumber ' As String
  Dim lngNumber ' As Long

  strNumber = replace(varNumber,"+","")
  strNumber = replace(strNumber,"(","")
  strNumber = replace(strNumber,")","")
  strNumber = replace(strNumber," ","")
  
  If isNumeric(strNumber) Then
     lngNumber = clng(trim(strNumber))
     If lngNumber < 100000 Then 
        isTelephone = false
     Else
        isTelephone = true
     End If
  Else
     isTelephone = false
  End If

End Function


'--------------------------------------------------------------------'
' 
'--------------------------------------------------------------------'
Function isEmail(varAddress)

  Dim intAtPos 'As Integer
  Dim intDotPos 'As Integer

  intAtPos  = instr(varAddress,"@")
  If intAtPos > 0 Then intDotPos = instr(intAtPos,varAddress,".")
    
  If (intAtPos = 0 Or intDotPos = 0) Or _
     (intAtPos = 1 Or intDotPos = 1) Or _
     (intAtPos = len(varAddress) Or intDotPos = len(varAddress)) Or _
     ((intDotPos - intAtPos) < 2)  Then
     isEmail = false
  Else
     isEmail = true
  End If

End Function


'--------------------------------------------------------------------'
' 
'--------------------------------------------------------------------'
Function isCCard(varCCard)

  Dim strCCNumber ' As String
  Dim intISub 'As Integer
  Dim intGTotal 'As Integer
  Dim intValue 'As Integer
  Dim strIPos 'As String

  isCCard = True

  intGTotal   = 0
  strCCNumber = trim(replace(varCCard," ",""))
	
  If isNumeric(strCCNumber) THEN
     strIPos = "odd"
     For intISub = len(strCCNumber) to 1 step -1
         intValue = cint(mid(strCCNumber,intISub,1))
         If strIPos = "odd" Then
            strIPos = "even"
         Else
            If intValue >= 5 Then
               intValue = (intValue * 2) - 9
            Else 
               intValue = (intValue * 2)
            End If
            strIPos = "odd"
         End If
         intGTotal = intGTotal + intValue
     Next
   
     If intGTotal mod 10 > 0 Then
        IsCCard = False
     End If
  Else
     IsCCard = False
  End If

End Function

'--------------------------------------------------------------------'
' loop through the input fields checking for any SELECTs that need  
' expanding with data from a database table
'  form element is LOOKUP attr:
'       connection  ODBC connection name
'       table       table name
'       display     field name to display      
'       value       field name to use as value  
'       where       additional where statement to retrieve record 
'--------------------------------------------------------------------'
Sub expandLookUps()

  Dim objConnection ' As Object
  Dim objRS ' As Object
  Dim objLookUpList ' As Object
  Dim objInput ' As Object
  Dim objLookUp ' As Object
  Dim objOption ' As Object
  Dim strConnection ' As String
  Dim strTable ' As String
  Dim strDisplay ' As String
  Dim strValue ' As String
  Dim strSQL ' As String  
  Dim objAttrList ' As String
  Dim objAttr ' As String
  Dim strWhere ' As String
  Dim booFirstOption ' As Boolean

  '---- create list of LOOKUP elements ----'
  Set objLookUpList = objForm.selectNodes("//LOOKUP")

  If objLookUpList.length > 0 Then 
  
     For each objLookUp in objLookUpList

         '---- create list of attributes ----' 
         Set objAttrList = objLookUp.attributes
                  
         '---- loop thorugh attributes and assign ----'
         For each objAttr in objAttrList
             Select Case lcase(objAttr.nodeName)
               Case "connection"
                 strConnection = objAttr.nodeValue
               Case "table"
                 strTable      = objAttr.nodeValue
               Case "display"   
                 strDisplay    = objAttr.nodeValue
               Case "value"
                 strValue      = objAttr.nodeValue
               Case "where"
                 strWhere      = objAttr.nodeValue
             End Select
         Next
              
         '---- create connection object ----'        
         Set objConnection = CreateObject("adodb.connection")
         objConnection.Open "DSN=" & strConnection

         '---- build SQL statement ----'
         strSQL = "SELECT " & strValue  
         
         If strDisplay <> strValue Then 
            strSQL = strSQL & "," & strDisplay 
         End IF   
            
         strSQL = strSQL & " FROM " & strTable
         
         If len(strWhere) > 0 Then
            strSQL = strSQL & " WHERE " & strWhere
         End If
      
         '---- create recordset by executing the query ----'
         Set objRS = objConnection.Execute(strSQL)

         booFirstOption = true

         While NOT objRS.eof
            Set objOption  = objForm.createElement("OPTION")
            If booFirstOption Then 
               objOption.setAttribute "selected", "yes"
               booFirstOption = false
            End If
            objOption.setAttribute "value", objRS(strValue)
            objOption.text = objRS(strDisplay)
            Set objInput   = objLookUp.parentNode
            objInput.appendChild objOption
            objRS.moveNext
         Wend
     
     Next
  
  End If   

End Sub

'--------------------------------------------------------------------'
' loop through the input fields that have an initial attribute and set 
' the value accordingly  
'--------------------------------------------------------------------'
Sub initFields()

  Dim objInput ' As Object
  Dim objInputList ' As Object

  '---- create list of FIELD elements ----'
  Set objInputList = objForm.selectNodes("//FIELD[@initial != '']")

  If objInputList.length > 0 Then 
  
     For each objInput in objInputList

         '---- check value of init attribute ----'
         Select Case lcase(objInput.getAttribute("initial"))
            Case "today"
               objInput.setAttribute "value",day(now) & "/" & month(now)& "/" & year(now)
            Case "time"
               objInput.setAttribute "value",hour(now) & ":" & minute(now)& ":" & second(now)
            Case "now"
               objInput.setAttribute "value",day(now) & "/" & month(now)& "/" & year(now) & " " & hour(now) & ":" & minute(now)& ":" & second(now)
            Case Else  
               objInput.setAttribute "value",objInput.getAttribute("initial")
         End Select
         
     Next

  End If   

End Sub
    
'--------------------------------------------------------------------'
' 
'--------------------------------------------------------------------'
'Sub setStatus(varStatus)
'
'  Dim objStatus 'As Object
'  
'  objForm.documentElement.setAttribute "status", varStatus
'
'End Sub

'--------------------------------------------------------------------'
' 
'--------------------------------------------------------------------'
Sub writeError (varObj,varErrorMsg)

  Dim objNewError 'As Object
  Dim objFormErrors ' As Object

  If objForm.selectNodes("//FORM-ERRORS").length = 0 Then
     Set objFormErrors = objForm.createElement("FORM-ERRORS")
     objForm.documentElement.appendChild (objFormErrors)
  End If
  
  Set objFormErrors = objForm.selectSingleNode("//FORM-ERRORS")
    
  Set objNewError = objForm.createElement("ERROR")
  objFormErrors.appendChild (objNewError)
  
  objNewError.setAttribute "message",varErrorMsg
  
  If varObj.getAttribute("label") <> "" Then 
     objNewError.setAttribute "name",varObj.getAttribute("label")
  Else
     objNewError.setAttribute "name",""
  End If
    
  varObj.setAttribute "error","yes"
 
End Sub

'-----------------------------------------------------------' 
' Common function to load in XML file and check for errors'
'-----------------------------------------------------------' 
Function loadFileXml (xmlObject)

  xmlObject.async = False
  
  If xmlObject.loadXML(strXmlDB) Then 
'     Response.Write ("Debug loadXML strXmlDB <BR/>")
     loadFileXml = true
  Else
     loadFileXml = false
     xmlObject.loadXML("<ERROR " & _
                  "msg='" & strXmlDB & " did not load correctly'" & _
                  " desc='" & xmlObject.parseError.reason & "'" & _
                  " line='" & xmlObject.parseError.line & "'" & _
                  "/>")
  End If

End Function

'-----------------------------------------------------------' 
' Common function to load in XML file and check for errors'
'-----------------------------------------------------------' 
Function loadFileXsl (xmlObject)

  xmlObject.async = False
  
  If xmlObject.loadXML(strXslDB) Then 
'    Response.Write ("Debug loadXML strXslDB  ok <BR/>")
    loadFileXsl = true
  Else
     loadFileXsl = false
     xmlObject.loadXML("<ERROR " & _
                  "msg='" & strXmlDB & " did not load correctly'" & _
                  " desc='" & xmlObject.parseError.reason & "'" & _
                  " line='" & xmlObject.parseError.line & "'" & _
                  "/>")
  End If

End Function

'--------------------------------------------------------------------'
' loadfile from db  
'--------------------------------------------------------------------'
Function loadFileDB(MSGID)

  Dim objConnection ' As Object
  Dim objRS ' As Object
  Dim strTable ' As String
  Dim strSQL ' As String  
  Dim strWhere ' As String

  strTable      = "SPB_XMLXSL"
  strSQL        = "SELECT MSG_ID, FORM_XML, FORM_XSL FROM " & strTable 
  strWhere      = " WHERE MSG_ID = '" & MSGID & "'"
      
'  Response.Write ("Debug loadFileDB INICIO: <BR/>")
 
  strSQL = strSQL & strWhere
'  Response.Write ("Debug loadFileDB strSQL: " & strSQL & " <BR/>")

        '---- create connection object ----'        
  Set objConnection = CreateObject("adodb.connection")

  objConnection.Open strDBConnection
'  objConnection.Open "Provider=SQLOLEDB;Initial Catalog=BCSPBSTR;Data Source=SRVCX077", "SA", "SQLADM"

   
  Set objRS = objConnection.Execute(strSQL)

  While NOT objRS.eof
       strXmlDB = objRS("FORM_XML")
'       Response.Write ("Debug loadFileDB FORMXML <BR/>")
       strXslDB = objRS("FORM_XSL")
'       Response.Write ("Debug loadFileDB FORMXSL <BR/>")
       objRS.moveNext
  Wend
  objRS.close
  objConnection.close
End Function
%>