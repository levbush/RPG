from classes import *
# Create Player, Mob, Quest, world, and inventory

quest1, quest2, quest3 = Quest(
        name="Slay the Bandit Leader",
        giver="Eldora, Warrior of the Warriors Order",
        storyline="A dangerous bandit leader has been terrorizing the region. End his reign of terror.",
        objectives=["Find the Bandit Camp", "Defeat the Bandit Leader"],
        rewards=[Weapon(name='Bandit Leader\'s Axe', description='A powerful axe wielded by the bandit leader.', quality='Legendary', damage=100.0)],
        reputation = 5,
        gold = 100
    ), Quest(
        name="Recover the Lost Relic",
        giver="Galen, Mage of the Mages Guild",
        storyline="An ancient relic was stolen by thieves and must be recovered before it falls into the wrong hands.",
        objectives=["Investigate the Theft", "Locate the Thieves' Hideout", "Recover the Relic"],
        rewards=["200 Gold", "Mage's Favor"],
    ), Quest(
        name="Save the Trapped Miners",
        giver="Ironhold Miner Guild",
        storyline="A group of miners are trapped after a cave-in. Rescue them before supplies run out.",
        objectives=["Enter the Collapsed Mines", "Clear the Rubble", "Escort the Miners to Safety"],
        rewards=["300 Gold", "Free Access to Mines"],
    )
# quests = [
#     quest1, quest2, quest3
# ]

recipes = [
    {
        "name": "Iron Sword",
        "requirements": ["Iron Ore", "Wood"],
        "result": Weapon(name="Iron Sword", description="A sturdy iron sword.", quality="Uncommon", damage=20),
    },
    {
        "name": "Health Potion",
        "requirements": ["Herbs", "Water"],
        "result": Item(name="Health Potion", description="Restores health.", quality="Common"),
    },
]
crafting_stations = [
    CraftingStation(name="Blacksmith Forge", station_type="Forge", x=300, y=300),
    CraftingStation(name="Alchemy Table", station_type="Alchemy", x=500, y=500)
]

city1 = City(
    name="Ironhold",
    population=5000,
    guards=200,
    faction=Faction("Warriors Order"),
    shops=[],
    crafting_stations=crafting_stations,
    x=300,
    y=400
)




mob = Mob("Library Guardian", x=200, y=200, health=30, max_health=30, damage=50, trigger=quests[0], loot=Item(name="Book of Knowledge", description="A book containing ancient knowledge.", quality="Legendary"))

# mob1, mob2, mob3, mob4 = Mob(name="Goblin Raider", health=50, damage=10, loot=Item('Goblin Spear'), level=3),Mob(name="Sand Wyrm", health=200, damage=25, loot=Item('Wyrm scale'), level=7),Mob(name="Forest Troll", health=300, damage=30, loot=Item("Troll Hide"), level=10),Mob(name="Dune Leviathan", health=1000, damage=50, loot=Item("Leviathan Claw"), level=20, is_boss=True, trigger=quest1),
# mobs = [
#     mob1, mob2, mob3, mob4
# ]
mobs = [mob, Mob(name="Goblin Raider", health=50, damage=10, loot=Item('Goblin Spear'), level=3, x=500, y=200)]

# Example items
health_potion = Item(name="Health Potion", description="Restores 50 health.", quality="Common", price=10)
mana_potion = Item(name="Mana Potion", description="Restores 50 mana.", quality="Common", price=15)
sword = Weapon(name="Steel Sword", description="A sharp steel blade.", quality="Uncommon", damage=25, price=50)

# Example shops
potion_shop = Shop(name="Potion Shop", items=[health_potion, mana_potion])
weapon_shop = Shop(name="Weapon Shop", items=[sword])
city1 = City(
    name="Ironhold",
    population=5000,
    guards=200,
    crafting_stations=crafting_stations,
    x=300,
    y=400,
    faction=Faction("Warriors Order"),
    shops=[potion_shop, weapon_shop]
)

cities = [city1]

npcs = [
    NPC(name="Max", quests=[quest1], x=300, y=300),
    NPC(name="Eldora", quests=[quest2], x=400, y=400)
]
player = Character("Eldrin",  None,'Warrior', skills=[Skill('Fireball', 'damage', 100, 10)])
inventory = Inventory(player)
player.inventory = inventory
npcs.append(NPC("Galen", quests=[quests[0]], x=500, y=500))
world = World('Eldoria', cities, npcs, mobs)
running = True
while running:
    screen.fill(WHITE)
    font = pygame.font.Font(None, 36)
    # Event Handling
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN:
            if player.alive:
                for mob in mobs:
                    if abs(player.x - mob.x) < 50 and abs(player.y - mob.y) < 50:
                        if event.key == K_1:  # Special ability key
                            if len(player.skills) > 0:
                                player.use_skill(player.skills[0], mob)
                        if event.key == K_2:  # Special ability key
                            if len(player.skills) > 1:
                                player.use_skill(player.skills[1], mob)
                        if event.key == K_3:  # Special ability key
                            if len(player.skills) > 2:
                                player.use_skill(player.skills[2], mob)
                        if event.key == K_4:  # Special ability key
                            if len(player.skills) > 3:
                                player.use_skill(player.skills[3], mob)
                        if event.key == K_5:  # Special ability key
                            if len(player.skills) > 4:
                                player.use_skill(player.skills[4], mob)
                        if event.key == K_SPACE and player.alive:
                            player.attack(mob)
                if event.type == KEYDOWN and event.key == K_i:
                    render_inventory_menu(screen, player)
                for npc in npcs:
                    if abs(player.x - npc.x) < 50 and abs(player.y - npc.y) < 50:
                        if event.type == KEYDOWN and event.key == K_e:
                            npc.give_quest(player)
                for city in cities:
                    if abs(player.x - city.x) < 50 and abs(player.y - city.y) < 50:
                        if event.type == KEYDOWN and event.key == K_e:
                            city.enter(screen, city, player)
                if event.key == K_r:
                    player.rest(5)
            if event.key == K_q:
                print("Quests:")
                for quest in player.quests:
                    print(f" - {quest.name}")

    # Player Movement
    keys = pygame.key.get_pressed()
    if player.alive and not player.resting:  # Only allow movement if the player is alive and not resting
        player.move(keys)
    # Draw Entities (only alive ones will be drawn)
    player.draw(screen)
    for mob in mobs:
        mob.draw(screen)
    for npc in npcs:
        npc.draw(screen)
        if abs(player.x - npc.x) < 50 and abs(player.y - npc.y) < 50:
            npc_font = pygame.font.Font(None, 24)
            text = npc_font.render(npc.name, True, (0, 0, 0))
            npc_text = npc_font.render(f"Press E to interact", True, BLACK)
            screen.blit(npc_text, (npc.x, npc.y - 30))
    for city in cities:
        city.draw(screen)
        if abs(player.x - city.x) < 50 and abs(player.y - city.y) < 50:
            city_font = pygame.font.Font(None, 24)
            city_text = city_font.render(f"Press E to enter", True, BLACK)
            screen.blit(city_text, (city.x - 5, city.y - 35))

            # Check for city interaction
            for event in pygame.event.get():
                if event.type == KEYDOWN and event.key == K_e:
                    city.enter(player, screen)

    # Display Quest Info
    if player.quests:
        quest_text = font.render(f"Quest: {player.active_quest.name}", True, BLACK)
        screen.blit(quest_text, (10, 10))
    
    if not player.alive:
        display_notification(f"{player.name} has died!", RED)


    if player.active_quest:
        if not player.active_quest.completed:
            objective_text = font.render(
                f"Objective: {player.active_quest.objectives[player.active_quest.current_objective]}",
                True, BLACK
            )
            screen.blit(objective_text, (10, 50))
        else:
            completed_text = font.render("Quest Complete!", True, GREEN)
            screen.blit(completed_text, (10, 50))

    
    health_text = font.render(f"Health: {player.health}/{player.max_health}", True, RED)
    mana_text = font.render(f"Mana: {player.mana}/{player.max_mana}", True, BLUE)
    screen.blit(health_text, (10, 90))
    screen.blit(mana_text, (10, 130))
    # Draw the minimap on the main screen
    minimap = pygame.Surface((150, 150))
    minimap.fill(BLACK)

    # Scale down positions for minimap (10:1 ratio)
    pygame.draw.circle(minimap, GREEN, (player.x // 10, player.y // 10), 5)  # Player position
    for city in cities:
        pygame.draw.circle(minimap, BLUE, (city.x // 10, city.y // 10), 5)  # Cities
    for mob in mobs:
        if mob.alive:
            pygame.draw.circle(minimap, RED, (mob.x // 10, mob.y // 10), 5)  # Mobs
    for npc in npcs:
        pygame.draw.circle(minimap, BLUE, (npc.x // 10, npc.y // 10), 5)  # NPCs

    # Display the minimap
    screen.blit(minimap, (SCREEN_WIDTH - 170, 20))


    for mob in mobs:
        if random.random() < 0.0001:  # 0.01% chance per tick
            mob.migrate()

    if pygame.time.get_ticks() % 20000 == 0:  # Every 20 seconds
        world.update_world()

    # Update Screen
    pygame.display.flip()
    clock.tick(60)

pygame.quit()