-- Dialogue System
local DialogueSystem = { Properties = { DialogueAsset = { default = "" } } }
function DialogueSystem:OnActivate()
    self.isActive = false
    self.currentLine = 0
    self.lines = {}
end
function DialogueSystem:OnDeactivate() end
function DialogueSystem:StartDialogue(lines)
    self.lines = lines
    self.currentLine = 1
    self.isActive = true
    self:ShowLine()
end
function DialogueSystem:ShowLine()
    if self.currentLine <= #self.lines then
        local line = self.lines[self.currentLine]
        Debug.Log(line.speaker .. ": " .. line.text)
    else
        self:EndDialogue()
    end
end
function DialogueSystem:Advance()
    self.currentLine = self.currentLine + 1
    self:ShowLine()
end
function DialogueSystem:EndDialogue()
    self.isActive = false
    self.currentLine = 0
end
