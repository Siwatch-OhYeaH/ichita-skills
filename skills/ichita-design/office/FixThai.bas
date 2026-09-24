Attribute VB_Name = "FixThai"
' ICHITA — one-click fix for Thai in Word.
' Same effect as "paste as plain text" (resets the wrong language tag), but keeps
' bold/italic/links and runs on the whole document, headers and footers included.
' Install: Alt+F11 > File > Import File > FixThai.bas (into Normal), then
' File > Options > Quick Access Toolbar > Macros > FixThai > Add.

Public Sub FixThai()
    Dim story As Range, p As Paragraph
    Application.ScreenUpdating = False
    For Each story In ActiveDocument.StoryRanges
        Do While Not story Is Nothing
            FixRange story
            Set story = story.NextStoryRange
        Loop
    Next story
    ActiveDocument.SpellingChecked = False
    ActiveDocument.GrammarChecked = False
    Application.ScreenUpdating = True
    MsgBox "Thai language tag and alignment fixed.", vbInformation, "ICHITA"
End Sub

Private Sub FixRange(r As Range)
    Dim p As Paragraph
    r.LanguageID = wdThai            ' the actual fix: Thai dictionary + Thai word breaks
    r.NoProofing = False
    r.Font.NameBi = "TH Aeonik Book" ' font Word uses for Thai (complex script)
    For Each p In r.Paragraphs
        If p.Alignment = wdAlignParagraphJustify Or p.Alignment = wdAlignParagraphDistribute Then
            If HasThai(p.Range.Text) Then p.Alignment = wdAlignParagraphThaiJustify
        End If
        ' Shift+Enter line breaks inside Thai paragraphs cause stretched lines
        If HasThai(p.Range.Text) Then
            With p.Range.Find
                .Text = "^l": .Replacement.Text = " ": .Forward = True
                .Wrap = wdFindStop: .Execute Replace:=wdReplaceAll
            End With
        End If
    Next p
    With r.Find                        ' NBSP -> normal space (TH Aeonik has no NBSP)
        .Text = "^s": .Replacement.Text = " ": .Wrap = wdFindStop
        .Execute Replace:=wdReplaceAll
    End With
End Sub

Private Function HasThai(s As String) As Boolean
    Dim i As Long, c As Long
    For i = 1 To Len(s)
        c = AscW(Mid$(s, i, 1))
        If c >= &HE00 And c <= &HE7F Then HasThai = True: Exit Function
    Next i
End Function
