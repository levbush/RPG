from classes import *

# Create Camera
camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

# Define recipes
recipes = [
    Recipe(
        name="Iron Sword",
        ingredients=[(Item("Iron Ore"), 3), (Item("Wood"), 2)],
        result=Weapon(name="Iron Sword", description="A sturdy iron sword.", quality="Uncommon", damage=20),
        required_station="Forge",
        experience=100
    ),
    Recipe(
        name="Health Potion",
        ingredients=[(Item("Herbs"), 3), (Item("Water"), 1)],
        result=Potion(name="Health Potion", description="Restores health.", quality="Common", potion_type="Heal", value=30),
        required_station="Alchemy",
        experience=50
    ),
]

# Define crafting stations
crafting_stations = [
    CraftingStation(name="Blacksmith Forge", station_type="Forge"),
    CraftingStation(name="Alchemy Table", station_type="Alchemy")
]

# Define factions
guild_of_merchants = Faction(name="Guild of Merchants", description="A coalition of traders and shopkeepers.")
dark_brotherhood = Faction(name="Dark Brotherhood", description="A secretive guild of assassins.", base_reputation=-10)

# Define player and inventory
player = Character(name="Eldrin", inventory=None, character_class="Warrior", skills=[Skill('Fireball', 'damage', 100, 10)])
player_inventory = Inventory(player, known_recipes=recipes)
player.inventory = player_inventory

# Add items and recipes to inventory
player.inventory.add_recipe(recipes[0])
player.inventory.add_recipe(recipes[1])
player.inventory.add_item(Item("Wood"), 10)
player.inventory.add_item(Item("Iron Ore"), 10)

# Define mobs
mobs = [
    Mob(
        name="Library Guardian", x=200, y=200, health=30, max_health=30, damage=50,
        trigger=Quest(
            name="Rescue the Merchant", giver="Elder Doran", storyline="Rescue the merchant captured by bandits.",
            objectives=["Defeat the bandits", "Rescue the merchant"],
            rewards=[Item(name="Book of Knowledge", description="Contains ancient knowledge.", quality="Legendary")],
            faction_rewards={"Guild of Merchants": 30}
        ),
        loot=Item(name="Book of Knowledge", description="A book containing ancient knowledge.", quality="Legendary")
    ),
    Mob(name="Goblin Raider", health=50, damage=10, loot=Item('Goblin Spear'), level=3, x=500, y=200)
]

# Define cities
cities = [
    City(
        name="Ironhold", population=5000, guards=200, faction=guild_of_merchants,
        shops=[Shop(name="Merchant's Haven", items=[Item('Oak Wood', price=10), Potion('Mana potion', potion_type='Mana', price=15), Potion('Health Potion', price=15),], faction=guild_of_merchants)],
        crafting_stations=crafting_stations, x=300, y=400
    )
]

# Define NPCs
npcs = [
    NPC(name="Eldora", quests=[], x=400, y=400),
    NPC(name="Galen", quests=[mobs[0].trigger], x=500, y=500)
]

# Define world
world = GameWorld(width=2000, height=2000, num_resources=20)

# Adjust player reputation
player.adjust_reputation(guild_of_merchants, 50)
player.adjust_reputation(dark_brotherhood, -15)


# Main Game Loop
running = True
while running:
    screen.fill(WHITE)  # Clear the screen

    # try:
        # Handle events
    if player.alive and not player.resting:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                # Open inventory
                if event.key == K_e:
                    render_inventory_menu(screen, player)
                # Display active quests
                elif event.key == K_q:
                    print("Quests:")
                    for quest in player.quests:
                        print(f" - {quest.name}")
                # Attack nearby mobs
                elif event.key == K_SPACE:
                    for mob in mobs:
                        if abs(player.x - mob.x) < 50 and abs(player.y - mob.y) < 50:
                            player.attack(mob)
                # Interact with cities and NPCs
                elif event.key == K_f:
                    # Interact with cities
                    for city in cities:
                        if abs(player.x - city.x) < 50 and abs(player.y - city.y) < 50:
                            city.enter(player, screen)
                    # Interact with NPCs
                    for npc in npcs:
                        if abs(player.x - npc.x) < 50 and abs(player.y - npc.y) < 50:
                            npc.interact(player)
                    # Interact with resources
                    for resource in world.resources:
                        if abs(player.x - resource.x) < 50 and abs(player.y - resource.y) < 50:
                            player.collect_resource(resource)

    # Handle player movement
    if player.alive and not player.resting:
        keys = pygame.key.get_pressed()
        player.move(keys)
        camera.center_on(player)  # Center the camera on the player

        # Draw player
        screen_x, screen_y = camera.apply(player)

        # Check if the player is within screen bounds

        pygame.draw.rect(screen, player.color, (screen_x, screen_y, 30, 30))  # Green square for the player

        font = pygame.font.Font(None, 24)
        name_surface = font.render(player.name, True, BLACK)
        screen.blit(name_surface, (screen_x, screen_y - 20))  # Render player name above

    for entity in mobs + npcs:
        # if is_within_view(camera, entity):
        screen_x, screen_y = camera.apply(entity)
        # Render entity using screen coordinates
        entity.draw_at(screen, (screen_x, screen_y))


    # Draw resources
    for resource in world.resources:  # Limit to first 5 resources
        if not resource.collected:
            res_x, res_y = camera.apply(resource)

            # Check if resource is within screen bounds
            # if 0 <= res_x <= SCREEN_WIDTH and 0 <= res_y <= SCREEN_HEIGHT:
            pygame.draw.circle(screen, (0, 255, 0), (res_x, res_y), 10)  # Green circle for resources

            # Display resource name above the resource
            resource_name_surface = font.render(f"{resource.resource_type} ({resource.quantity})", True, BLACK)
            screen.blit(resource_name_surface, (res_x, res_y - 20))

    # Display interaction tooltip
    tooltip = None
    for mob in mobs:
        if abs(player.x - mob.x) < 50 and abs(player.y - mob.y) < 50:
            tooltip = f"Press SPACE to attack {mob.name}"
    for npc in npcs:
        if abs(player.x - npc.x) < 50 and abs(player.y - npc.y) < 50:
            tooltip = f"Press F to talk to {npc.name}"
    for city in cities:
        if abs(player.x - city.x) < 50 and abs(player.y - city.y) < 50:
            tooltip = f"Press F to enter {city.name}"
    for resource in world.resources:  # Check first 5 resources
        if not resource.collected and abs(player.x - resource.x) < 50 and abs(player.y - resource.y) < 50:
            tooltip = f"Press F to collect {resource.resource_type}"

    # Render tooltip if applicable
    if tooltip:
        tooltip_surface = font.render(tooltip, True, BLACK)
        screen.blit(tooltip_surface, (10, SCREEN_HEIGHT - 40))  # Show tooltip at the bottom of the screen

    # Render logger messages
    logger.render(10, SCREEN_HEIGHT - 200)

    # Update the display
    pygame.display.flip()
    clock.tick(60)  # Limit to 60 FPS

    # except Exception as e:
    #     print(f"Error occurred: {e}")
    #     running = False

pygame.quit()
