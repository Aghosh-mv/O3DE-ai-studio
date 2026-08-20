-- Player Controller
local PlayerController = { Properties = { Speed = { default = 5.0 }, Health = { default = 100 } } }
function PlayerController:OnActivate()
    self.tickHandler = TickBus.Connect(self, 0)
    self.hp = self.Properties.Health
end
function PlayerController:OnDeactivate() self.tickHandler:Disconnect() end
function PlayerController:OnTick(dt, tp)
    local input = Vector3(0, 0, 0)
    if InputDevice.IsKeyDown("keyboard_w") then input = input + Vector3(0, 1, 0) end
    if InputDevice.IsKeyDown("keyboard_s") then input = input + Vector3(0, -1, 0) end
    if InputDevice.IsKeyDown("keyboard_a") then input = input + Vector3(-1, 0, 0) end
    if InputDevice.IsKeyDown("keyboard_d") then input = input + Vector3(1, 0, 0) end
    if input:GetLength() > 0 then input = input:GetNormalized() end
    local pos = TransformBus.Event.GetLocalTranslation(self.entityId)
    TransformBus.Event.SetLocalTranslation(self.entityId, pos + input * self.Properties.Speed * dt)
end
