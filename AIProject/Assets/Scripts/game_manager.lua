-- Game Manager
local GameManager = { Properties = { GameState = { default = "menu" } } }
function GameManager:OnActivate()
    Debug.Log("Game Manager initialized")
    self.score = 0
    self.wave = 1
    self.tickHandler = TickBus.Connect(self, 0)
end
function GameManager:OnDeactivate() self.tickHandler:Disconnect() end
function GameManager:OnTick(dt, tp) end
function GameManager:AddScore(amount) self.score = self.score + amount end
function GameManager:NextWave() self.wave = self.wave + 1; Debug.Log("Wave " .. self.wave) end
