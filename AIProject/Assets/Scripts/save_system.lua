-- Save System
local SaveSystem = { Properties = { SaveFileName = { default = "savegame.json" } } }
function SaveSystem:OnActivate() end
function SaveSystem:OnDeactivate() end
function SaveSystem:SaveGame(data)
    local path = self.Properties.SaveFileName
    Debug.Log("Game saved to " .. path)
end
function SaveSystem:LoadGame()
    Debug.Log("Game loaded")
end
