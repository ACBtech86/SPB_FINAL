<?xml version="1.0"?>

<!-- Note that this stylesheet relies on the XMLDocument and XSLDocument properties and thus
     only works when browsing XML -->

  
<xsl:stylesheet xmlns:xsl="http://www.w3.org/TR/WD-xsl">
  <xsl:template match="/">
     <STYLE>
          BODY {margin:0}
          .fntPagina {font:8pt Verdana; background-color:white; color:blue}
          .fntLeftPag {font:8pt Times New Roman; background-color:white; color:black}
          H1 {font:bold 14pt Verdana; width:100%; margin-top:1em;color:gray}
          .fntfntLinhaTab {font:4pt Verdana; border-bottom:1px solid #CC88CC}
          .fntCabecTab {font:bold 8pt Verdana; cursor:hand; padding:2px; border:2px outset gray}
          .Cor_Erro {background-color:#FFBBBB;}		<!-- Vermelho -->
          .Cor_Aviso {background-color:#FFFFBB;}	<!-- Verde    -->
          .Cor_Normal {background-color:#DDFFDD;}	<!-- Verde    -->

		<!-- (N)ormal, (E)rro - Vermelho e (R)eport - Amarelo  -->
        </STYLE>  
  
     
      <SCRIPT><xsl:comment><![CDATA[

        function Classifica(coluna)
        {
          sortField.value = coluna;
          <!-- set cursor to watch here? -->
          listing.innerHTML = source.documentElement.transformNode(stylesheet);
        }

      ]]></xsl:comment></SCRIPT>


      <SCRIPT><xsl:comment><![CDATA[

		function shwCOD_MSG (codmsg)
		{	
			palette = window.open("","paletteWindow","toolbar=no,location=no, menubar=no,scrollbars=yes,resizable=yes,alwaysRaised");
			palette.location.href="http://srv-gersut:8089/SPB/ValidateMsg.asp?selectl=" + codmsg + "R1"
		}
		
		function shwReport(msg)
		{	
			palette = window.open("","paletteWindow","toolbar=no,location=no, menubar=no,scrollbars=yes,resizable=yes,alwaysRaised");
			palette.location.href="http://srv-gersut:8089/ShwMsg.asp?selectl=" + msg 
		}
      ]]></xsl:comment></SCRIPT>

      <SCRIPT LANGUAGE="JScript"><xsl:comment><![CDATA[
		
    // *********************************************************************
    // *  Constants declarations
    // *********************************************************************

    var blue = "#0000FF";
    var black = "#000000";
    var attributeColor = "green";
    var textColor = "red";
    var commentColor = "purple";

    var attID = "tv:TreeViewerID";   // Name of the attribute add to the
                                  // tree to point to the span id.
    var nsName = "msTreeViewer";  // Name of the namespace that will hold
                                  // the attribute that is added.

    var ELEMENT_NODE = 1;
    var ATTRIBUTE_NODE = 2;
    var NAMESPACE_NODE = 7;       // 7 is for processing instruction.
    var TEXT_NODE = 3;
    var COMMENT_NODE = 8;
    var CDATA_NODE = 4;
    var ENTITYREF_NODE = 5;


    // *********************************************************************
    // *  Variable declarations 
    // *********************************************************************

    var strStruct;            // string that holds the html version of the tree.
    var elementNum;           // Counter to keep track of what to call the
                              // span id in the html display version of
                              // the tree.
    var code;                 // Array that holds information about whether
                              // to display the | or not.
    var selectedNodes;        // Keeps track of which nodes are highlighted.
    var selectedNodesType;
    var selectedNodesLength;  // Keeps track of how many nodes are highlighted.
    var displayFrame;         // display frame (displayFrame = parent.display)
    var treeViewNS = "urn:tv";// The Tree Viewer namespace node.
    var tempNode;             // Used by user in executeString.



    // *********************************************************************
    // *  Helper functions 
    // *********************************************************************

    // Reset on reload.
    function windowLoad()
    {
      displayFrame = parent.display;

      displayFrame.document.open();
      displayFrame.document.write("");            
      displayFrame.document.close();

      selectionString.value = "";
      XMLFile.focus();
    }

    // Automatically click button when user presses enter.
    function loadEnter()
    {
      if (event.keyCode == 13)        // 13 is keyCode for enter.
      {
        loadButton.click();
        selectionString.focus();
      }
    }

    // Automatically click button when user presses enter.
    function selectionEnter()
    {
      if (event.keyCode == 13)
        selectionButton.click();
    }



// ***********************************************************************
// *  Selection highlighting functions 
// ***********************************************************************

    // Called by the 'Display Selection' button.
    // Unhighlights the previously highlighted nodes.
    // Decides if the entry points to an attribute node, element node or node list and calls
    // the appropriate handler.

    function genericSelect()
    {
      if (xmldoc == null)
      {
        alert("No xml file has been loaded.");
        selectionString.value = "";
      }
      else
      {
        // Only choices are nodeList, node or attributes.
        // This try...catch block needs JScript version 5 which comes with IE5.
        try
        {
          selection = eval(selectionString.value);
        }
        catch(e)
        {
          selection = null;
        }

        if (selection == null)
          alert("Only element nodes, attribute nodes and node lists can be specified.");
        else
        {
          // Unselect previously selected nodes.
          if (selectedNodesLength != 0)
          {
            for (var i = 0; i < selectedNodesLength; i++)
            {
              if (selectedNodesType[i] == "attribute")
                parent.display.document.all.item(selectedNodes[i]).style.color = attributeColor;
              else
                parent.display.document.all.item(selectedNodes[i]).style.color = black;
            }
          }

          selectedNodesLength = 0;

          // Call appropriate handler.

          if (selection.length != null)  // Note this is also true for 
                                              //strings and other non nodeLists.
            selectNodeList(selection);
          else if (selection.nodeTypeString == "element")  
            selectNode(selection);
          else if (selection.nodeTypeString == "attribute")    
            selectAtt(selection);
          else
            alert("Only element nodes, attribute nodes and node lists can be specified.");
        }
      }
    }

    // Highlight an attribute node.
    //
    // Since attributes can't have attributes, they are counted off
    // from the parent element.

    function selectAtt(att)
    {
      var elem = att.selectSingleNode("ancestor(.)");

      attNum = elem.attributes.length;

      // Find the offset for the attribute.

      for (var i = 0; i < attNum; i++)
        if (elem.attributes.item(i).nodeName == att.nodeName)
          break;

      if (elem.attributes.getNamedItem(attID) != null) {
        var nodeID = elem.attributes.getNamedItem(attID).nodeValue + "_att_" + i;
        selectedNodes[selectedNodesLength] = nodeID;
        selectedNodesType[selectedNodesLength] = "attribute";    
        selectedNodesLength++;
        parent.frames("display").document.all(nodeID).style.color = blue;
      }
    }

    // Highlight an element node.
    function selectNode(node)
    {
      var nodeID;
      if (node.attributes.getNamedItem(attID) != null) {
        nodeID = node.attributes.getNamedItem(attID).nodeValue;
        selectedNodes[selectedNodesLength] = nodeID;
        selectedNodesType[selectedNodesLength] = "element"; 
        selectedNodesLength++;
        parent.display.document.all(nodeID).style.color = blue;
	  }
    }

    // Highlight a node list.
    function selectNodeList(list)
    {
      selectedNodesLength = list.length;

      for (var i = 0; i < list.length; i++)
      {
        // Only highlight elems and attrs (other stuff isn't in tree)
        if (list(i).nodeTypeString == "element")  
          selectNode(list(i));
        else if (list(i).nodeTypeString == "attribute")    
          selectAtt(list(i));
      }
    }

    // ********************************************************************
    // *  Tree loading and displaying functions 
    // ********************************************************************

    // Create the msxml object and load the specified xml file.
    function loadXML()
    {
      if (XMLFile.value == "")
      {
        alert("An xml file must be specified for loading to occur.");
      }
      else
      {
        xmldoc.async = false;
        xmldoc.load(XMLFile.value);

        if (xmldoc.parseError.errorCode != 0)
        {
          alert(errtxt);
          windowLoad();  
        }

        if (xmldoc.documentElement != null)
        {
          // Create the TreeViewer namespace here.

          //treeViewNS = xmldoc.createNode("attribute","xmlns:treeview", "");

          //treeViewNS = nsName;            // Setup the short name.

          //xmldoc.documentElement.attributes.setNamedItem(treeViewNS);
          //xmldoc.insertNode(treeViewNS);

          displayTree();
          selectionString.value = "xmldoc.";
        }
      }
    }

    // This function isolates the process of add the xml to the tree view.
    function addhtml(text)
    {
      strStruct += text;
    }

    // Use the recursive function buildTree to build the html
    // version of the tree. Display the tree in a seperate frame.

    function displayTree()
    {
      if (xmldoc == null)
      {
        alert("No xml file has been loaded.");
      }
      else
      {
        selectedNodes = new Array();
        selectedNodesType = new Array();
        selectedNodesLength = 0;

        //displayFrame = parent.display;
        //displayFrame.document.open();
        strStruct = "";

        //addhtml("<HTML><BODY BGCOLOR=\"#FFFFFF\">");  // #FFFFFF is white.
        elementNum = 0;
        code = new Array();
        //buildTree(xmldoc.documentElement, 0, ("XMLtree_" + elementNum),0);
        buildTree(xmldoc.documentElement, 0, 0);

        displayFrame.document.open();
        displayFrame.document.write(strStruct);            
        displayFrame.document.close();
      }
    }

    // buildTree is recursive.
    // level is the depth of the tree.
    // last is a boolean to tell the element if it's the last one
    // in the list. 1=true, 0=false.  The last one needs corner.gif.

    function buildTree(node, level, last)
    { 
      if (level != 0)
      {
        // Add | and whitespace

        for (var j = 0; j < (level-1); j++)
        {
          if (code[j] == 0)
            addhtml("<IMG SRC=\"vertical.gif\" ALIGN=\"absbottom\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;");
          else
            addhtml( "<IMG SRC=\"blank.gif\" ALIGN=\"absbottom\">&nbsp;&nbsp;&nbsp;");
        }

        // Add the appropriate corner piece.
        if (last == 1)
          addhtml("<IMG SRC=\"corner.gif\" ALIGN=\"absbottom\">&nbsp;");
        else
          addhtml("<IMG SRC=\"corner_continue.gif\" ALIGN=\"absbottom\">&nbsp;");
      }

      // Process a text node.
      if (node.nodeType == TEXT_NODE)
        addhtml("<FONT COLOR=\"" + textColor + "\">" + node.text + "</FONT>");
      else if (node.nodeType == COMMENT_NODE)
        addhtml("<FONT COLOR=\"" + commentColor + "\">" + node.text + "</FONT>");
      else
      {
        // Don't do the following on text nodes.  Don't give them
        // spans or check for attributes.

        // Make a span with a unique ID for each element to be able to
        // access them later.

        var elementID = "TreeViewer_" + elementNum;

        addhtml("<SPAN ID=\"" + elementID + "\">" + node.nodeName + "</SPAN>");

        elementNum++;    // Increment ID counter.

        // Put an attribute on each element that acts as pointers to
        // their corresponding span tags.

        //node.setAttribute(attID, elementID, treeViewNS);

        var tvNode = xmldoc.createNode("attribute",attID,treeViewNS);
        tvNode.text = elementID;
        node.attributes.setNamedItem(tvNode);

        // Display attributes
        var attNum = node.attributes.length;

        if (attNum > 0)
        {
          for (var i = 0; i < attNum; i++)
          {
            // Don't display attributes from the Tree Viewer namespace.
            if (node.attributes.item(i).namespace != null)
            {
              if (node.attributes.item(i).namespace != treeViewNS)
                addhtml("<B> ; </B><SPAN ID=\"" + elementID + "_att_" + i + "\" STYLE=\"color:green\">" + node.attributes.item(i).nodeName + "</SPAN>");
                 //+ " = \"" + node.attributes.item(i).text + "\"";
            }
            else
            {
              addhtml("<B> ; </B><SPAN ID=\"" + elementID + "_att_" + i + "\" STYLE=\"color:green\" >" + node.attributes.item(i).nodeName + "</SPAN>");        // + " = \"" + node.attributes.item(i).text + "\"";
            }
          }
        }
      }

      addhtml("<BR>");

      // If there are children under this node, call buildTree on them.
      var children = node.childNodes.length;
      if (children != 0)
      {
        for (var i = 0; i < children; i++)
        {
          if (i == (children - 1) )
          {
            // This case means we are at the last element.
            code[level] = 1;
            buildTree(node.childNodes.item(i), (level + 1), 1);
          }
          else
          {
            code[level] = 0;
            buildTree(node.childNodes.item(i), (level + 1), 0);
          }
        }
      }
    }

    // ********************************************************************
    // *  Displaying XML in a seperate window functions 
    // ********************************************************************


    function showXML(node)
    {
//     var xmldoc = new ActiveXObject("Msxml2.DOMDocument");
//     xmldoc.async = false;
//     var xmlmsg = node.text;
//     alert(xmlmsg);
//     xmldoc.loadXML(xmlmsg);

     if (xmldoc == null)
      {
        alert("No xml file has been loaded.");
      }
      else
      {
        var txtToShow = xmldoc.xml;
//        var txtToShow = dumpTree(xmldoc.documentElement, 0);
        var    wNew = window.open();
//        wNew.document.body.innerHTML = "<B>"+txtToShow+"</B>";
        wNew.document.body.innerHTML = txtToShow;
      }
    }

    // Format the XML into HTML
    function dumpTree(node, i)
    {
      var result = "<DL class=xml><DD>";

      if (node != null)
      {
        if (node.nodeTypeString == "comment")
        {
          result += "<span class=comment>&lt;!--" + node.text + "--&gt;</span>" + "</DD></DL>";
          return result;
        }

        result += "<span class=tag>&lt;" + node.nodeName + "</span>";

        // determine if the tag has children or is empty

        var num;

        // process the attributes
        if (node.attributes.length > 0)
        {
          var a, i, l;
          l = node.attributes.length;
          for (i = 0; i < l; i++)
          {
            a = node.attributes.item(i);
            // Don't display attributes from the Tree Viewer namespace.
            if (a.namespace != treeViewNS)
              result += "<span class=attr> " + a.nodeName + "=\"" + a.text + "\"</span>"
          }
        }    

        if (node.childNodes != null)
          num = node.childNodes.length;
        else
          num = 0;

        // close the element tag (if empty, use shorthand)

        if (num == 0)        // tag is empty
          result += "<span class=tag>/&gt;</span>";
        else
          result += "<span class=tag>&gt;</span>";

        // process the children of the element if it has any

        if (num > 0)    // tag has children
        {
          if (isMixed(node,num) > 0)
          { 
            result += node.text;
          }
          else
          {
            var j;
            for (j = 0; j < num; j++)
            {
              result += "\n";

              var child = node.childNodes.item(j);


// uncommented following line
              result += dumpTree(child,i + 1);
            }
          }

          result += "<span class=tag>&lt;/" + node.nodeName + "&gt;</span>\n";
        }
      }

      result += "</DD></DL>"
      return result;
    }

    // checks to see if all children of the element are
    // the same node type

    function isMixed(node,num)
    {
      var j;

      for (j = 0; j < num; j++)
      {
        var child = node.childNodes.item(j);

        var type = child.nodeTypeString;
        if (type == "text" || type == "cdata_section" ||
            type == "entity_reference")
          return 1;
      }

      return 0;
    }
		
      ]]></xsl:comment></SCRIPT>

      <SCRIPT for="window" event="onload"><xsl:comment><![CDATA[
          
          stylesheet = document.XSLDocument;
          source = document.XMLDocument;
      ]]></xsl:comment></SCRIPT>
      
        <TABLE width="100%" cellspacing="0">
          <TR>
            <TD class="fntPagina"/>
            <TD class="fntPagina">
                <H1><xsl:value-of select="MainTag/Cabecalho1"/>
                em <xsl:value-of select="MainTag/DataCorrente"/></H1>
            </TD>
          </TR>
          <TR>
            <TD class="fntLeftPag" width="120" valign="top">
              <P><xsl:eval>totalREQ(this)</xsl:eval></P>
              <P><xsl:eval>totalRSP(this)</xsl:eval></P>
              <P><B><xsl:eval>totalTrafego(this)</xsl:eval></B></P>
              <P>                                               </P>
              <P>Clique no cabecalho da coluna para classificar.</P>
              <P>                                               </P>
              <P>Clique nos botoes COD_MSG para apresentar a pagina da mensagem correspondente.</P>
            </TD>
            <TD class="fntPagina" valign="top">
               <DIV id="listing"><xsl:apply-templates select="MainTag"/></DIV>
            </TD>
          </TR>
        </TABLE>    
  </xsl:template>
  
  <xsl:template match="MainTag">

    <TABLE STYLE="font:8pt Verdana; background-color:white">
      
      <TCabecalho>      
<!--        <TD width="200"><DIV class="fntCabecTab">R1</DIV></TD>
-->       
        <TD width="80"><DIV class="fntCabecTab" onClick="Classifica('COD_MSG')">Cod_Msg</DIV></TD>
        <TD width="200"><DIV class="fntCabecTab" onClick="Classifica('DB_DATETIME')">Data_Hora_DataBase</DIV></TD>
        <TD width="80"><DIV class="fntCabecTab" onClick="Classifica('STATUS_MSG')">Status</DIV></TD>
        <TD width="80"><DIV class="fntCabecTab" onClick="Classifica('FLAG_PROC')">Proc</DIV></TD>
        <TD width="220"><DIV class="fntCabecTab" onClick="Classifica('MQ_QN_ORIGEM')">Fila_de_Origem</DIV></TD>
        <TD width="200"><DIV class="fntCabecTab" onClick="Classifica('MQ_DATETIME')">Data_Hora_MQ</DIV></TD>
        <TD width="200"><DIV class="fntCabecTab" onClick="Classifica('NU_OPE')">Num_Ope</DIV></TD>
        <TD width="80"><DIV class="fntCabecTab" onClick="Classifica('MSG')">Mensagem_XML</DIV></TD>
      </TCabecalho>
      
      <xsl:for-each select="EntryTag" order-by="DB_DATETIME">
        <TR>
 		  <xsl:choose>
		    <xsl:when test="STATUS_MSG[. $eq$ 'P']">
                <xsl:attribute name="class">Cor_Aviso</xsl:attribute>
		    </xsl:when>
		    <xsl:when test="STATUS_MSG[. $eq$ 'R']">
                <xsl:attribute name="class">Cor_Erro</xsl:attribute>
		    </xsl:when>
		    <xsl:when test="STATUS_MSG[. $eq$ 'E']">
                <xsl:attribute name="class">Cor_Erro</xsl:attribute>
		    </xsl:when>
		    <xsl:otherwise>
                <xsl:attribute name="class">Cor_Normal</xsl:attribute>
	        </xsl:otherwise>

		  </xsl:choose>
          <TD><DIV class="fntLinhaTab"><INPUT type="button" >
              <xsl:attribute name="value">
                  <xsl:apply-templates select="COD_MSG"/>
              </xsl:attribute>
 				<xsl:choose>
					<xsl:when test="COD_MSG[. $eq$ 'REPORT']">
						<xsl:attribute name="onclick">
                            shwReport(<![CDATA['<xsl:value-of select="MSG"/>]]>')
						</xsl:attribute>                                                                                      
					</xsl:when>
					<xsl:when test="COD_MSG[. $eq$ 'ERRO']">
						<xsl:attribute name="onclick">
                            shwReport('<![CDATA[<xsl:value-of select="MSG"/>]]>')
						</xsl:attribute>                                                                                      
					</xsl:when>
			    <xsl:otherwise>
					<xsl:attribute name="onclick">
					   showXML(<xsl:apply-templates select="MSG"/>)
					</xsl:attribute>                                                                                      
				</xsl:otherwise>

				</xsl:choose>
                                       </INPUT></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:apply-templates select="DB_DATETIME"/></DIV></TD>  
          <TD><DIV class="fntLinhaTab"><xsl:value-of select="STATUS_MSG"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:value-of select="FLAG_PROC"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:value-of select="MQ_QN_ORIGEM"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:apply-templates select="MQ_DATETIME"/></DIV></TD>
          <TD><DIV class="fntLinhaTab"><xsl:value-of select="NU_OPE"/></DIV></TD>
<!--
          <TD><DIV class="fntLinhaTab"><xsl:value-of select="COD_MSG"/></DIV></TD>
-->
          <TD><DIV class="fntLinhaTab"><xsl:apply-templates select="MSG"/></DIV></TD>
        </TR>
      </xsl:for-each>
    </TABLE>
  </xsl:template>


 <xsl:template match="MSG">
    <xsl:eval>NodeXML(this.text)</xsl:eval>
 </xsl:template>

 <xsl:template match="DB_DATETIME | MQ_DATETIME">
    <xsl:eval>FmtDataEuro(this.text)</xsl:eval>
  </xsl:template>

  <xsl:template match="COD_MSG">
    <xsl:eval>PadBlank(this.text,8)</xsl:eval>
  </xsl:template>

  <xsl:script><![CDATA[
    
    function totalTrafego(node)
    {
      totalTrafegado = node.selectNodes("/MainTag/EntryTag/DB_DATETIME");
      totalTrafegado = totalTrafegado.length;
      return formatNumber(totalTrafegado, "000") + " Msgs";
    }


    function totalREQ(node)
    {
      totalREQ = 0; 
      totalTrafegado = node.selectNodes("/MainTag/EntryTag/MQ_QN_ORIGEM");      
      for (v = totalTrafegado.nextNode(); v; v = totalTrafegado.nextNode())
		{
			fila = v.nodeTypedValue;
		    tipoFila = fila.substr(3,3);
	        if (tipoFila == "REQ")
			{
				totalREQ = totalREQ + 1;
			}
		}
      return formatNumber(totalREQ, "000") + " REQs";
    }
        
    
    function totalRSP(node)
    {
      totalRSP = 0; 
      totalTrafegado = node.selectNodes("/MainTag/EntryTag/MQ_QN_ORIGEM");
      for (v = totalTrafegado.nextNode(); v; v = totalTrafegado.nextNode())
		{
			fila = v.nodeTypedValue;
		    tipoFila = fila.substr(3,3);
	        if (tipoFila == "RSP")
			{
				totalRSP = totalRSP + 1;
			}
		}
      return formatNumber(totalRSP, "000") + " RSPs";
    }
    
    function FmtDataEuro(AAAAMMDDHHMMSS)
    {
	  Ano = AAAAMMDDHHMMSS.substr(0,4);
	  Mes = AAAAMMDDHHMMSS.substr(4,2);
	  Dia = AAAAMMDDHHMMSS.substr(6,2);
	  Horas = AAAAMMDDHHMMSS.substr(8,2);
	  Minutos = AAAAMMDDHHMMSS.substr(10,2);
	  Segundos = AAAAMMDDHHMMSS.substr(12,2);
	  DataFmt = Dia + "/" + Mes + "/" + Ano;
	  HoraFmt = Horas + ":" + Minutos + ":" + Segundos;
	  DataEuro = DataFmt + "." + HoraFmt;			
	  return DataEuro;
    }

    function PadBlank(texto,tam)
    {
	  textnew = texto;
	  lTxt = texto.length;
	  tam -= lTxt;
      for (var i = 0; i<tam; i++)
		{
			  textnew = textnew + " " 
        }
      return textnew.toUpperCase() ;
    }

    function TipoFila(fila)
    {
	  return fila.substr(3,3);
    }
   
   function NodeXML(strxml)
   {
	  textnew = strxml;
	  return textnew;
   }
   
   ]]></xsl:script>
   
</xsl:stylesheet>
