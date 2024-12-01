from random import randint
from dataclasses import dataclass
import pygame
from pygame.locals import *
import threading
import time
import random
# from collections import defaultdict
import builtins


pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("RPG game")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

clock = pygame.time.Clock()








class Faction:
    def __init__(self, name: str, description: str='', leader: 'Character'=None, members: list['Character']=[], base_reputation: int=0, influence: int=0):
        self.name = name
        self.description = description
        self.leader = leader
        self.members = members
        self.base_reputation = base_reputation
        self.influence = influence
    def gain_influence(self, amount):
        """Increase the faction's influence."""
        self.influence += amount
        if self.influence > 100:
            self.influence = 100
        print(f"{self.name}'s influence increased to {self.influence}.")

    def lose_influence(self, amount):
        """Decrease the faction's influence."""
        self.influence -= amount
        if self.influence < 0:
            self.influence = 0
        print(f"{self.name}'s influence decreased to {self.influence}.")

guild_of_merchants = Faction(name="Guild of Merchants", description="A coalition of traders and shopkeepers.")
dark_brotherhood = Faction(name="Dark Brotherhood", description="A secretive guild of assassins.", base_reputation=-10)
factions = [guild_of_merchants, dark_brotherhood]

@dataclass(unsafe_hash=True)
class Item:
    name: str
    description: str = ''
    requirements: dict = None
    quality: str = 'Common'
    trigger: 'Quest' = None # Quest that triggers the item
    price: int = None
    def trigger_quest(self, player: 'Character'):
        """Trigger the quest for the player."""
        if self.trigger: # Grant reward if available
            player.complete_quest(self.trigger)

@dataclass(unsafe_hash=True)
class Artifact(Item):
    name: str
    description: str = ''
    traits: dict=None

@dataclass(unsafe_hash=True)
class Weapon(Item):
    character_class: str = 'Warrior'
    damage: float = 10.0
    durskill: float = 100.0
    quality: str = 'Common'
    weapon_type: str = 'Weapon'

@dataclass(unsafe_hash=True)
class Sword(Weapon):
    length: float = 100.0

@dataclass(unsafe_hash=True)
class Wand(Weapon):
    weapon_type = 'Wand'
    item_type = 'Wand'
    range: float = 20.0


@dataclass(unsafe_hash=True)
class Armor(Item):
    character_class: str = 'Warrior'
    defense: float = 0.1
    health: float = 20.0
    agility: float = -5.0
    strength: float = 10.0
    durskill: float = 100.0
    quality: str = 'Common'
    slot: str = 'chest'


@dataclass(unsafe_hash=True)
class Shield(Weapon):
    weapon_type = 'Shield'

@dataclass(unsafe_hash=True)
class Food(Item):
    name: str = 'Food'
    health: float = 5.0
    saturation: float = 2.0
    item_type: str = 'Food'

@dataclass(unsafe_hash=True)
class Potion(Food):
    name: str = 'Potion'
    description: str = ''
    quality: str = 'Common'
    potion_type: str = 'Heal'
    value: float = 10.0
    item_type: str = 'Potion'
class Quest: 
    def __init__(self, name, giver, storyline, objectives, rewards: list, reputation: float = 0, gold: int = 10, experience: int = 50, faction_rewards: dict['Faction', int] = None, level: int = 1):
        self.name = name
        self.giver = giver
        self.storyline = storyline
        self.objectives = objectives  # List of objectives
        self.current_objective = 0    # Start from the first objective
        self.completed = False
        self.rewards = rewards
        self.reputation = reputation
        self.gold = gold
        self.experience = experience
        self.rewarded = False
        self.faction_rewards = faction_rewards or {}
        self.level = level

    def give_rewards(self, player: 'Character'):
        """
        Give the player the rewards after the quest is completed.
        """
        if self.completed:
            for reward in self.rewards:
                if player.inventory.capacity - len(player.inventory.contents) >= 1:
                    player.inventory.add_item(reward)
                    print(f"{player.name} received reward: {reward.name}.")
                else:
                    player.storage.add_item(reward)
                player.gold += self.gold
                print(f"Player {player.name} gained {self.gold} gold.")
                player.experience += self.experience
                print(f"Player {player.name} gained {self.experience} experience.")
                if len(player.quests) > 1:
                    player.accept_quest = player.quests[-1]
            for faction_name, rep_change in self.faction_rewards.items():
                faction = next(f for f in factions if f.name == faction_name)  # Find the faction by name
                player.adjust_reputation(faction, rep_change)

            self.rewarded = True
        else:
            print(f"Quest '{self.name}' is not completed. Rewards unavailable.")

class Shop:
    def __init__(self, name: str, items: list[Item], faction: 'Faction' = None):
        """
        Initialize a shop.
        :param name: Name of the shop.
        :param items: List of items available for purchase.
        :param faction: The faction that owns the shop (optional).
        """
        self.name = name
        self.items = items
        self.faction = faction

    def sell(self, player: 'Character', item_index: int):
        """
        Allow the player to sell an item to the shop.
        :param player: The player selling the item.
        :param item_index: The index of the item in the player's inventory to sell.
        """
        if item_index < 1 or item_index > len(player.inventory.contents):
            print("Invalid selection.")
            return

        item, quantity = player.inventory.contents[item_index - 1]
        price = getattr(item, 'price', 0)

        if price > 0:
            player.gold += price
            player.inventory.remove_item(item)
            print(f"You sold {item.name} for {price} gold.")
        else:
            print(f"{item.name} cannot be sold.")



quests = [Quest(name="Defeat the Guardian", storyline="Defeat the Library Guardian", objectives=["Defeat the Guardian"], rewards=[Wand('Wand', quality='Epic')], giver="Library Guardian")]


class CraftingStation:
    def __init__(self, name, station_type: str):
        """
        Initialize the crafting station.
        :param name: Name of the station (e.g., "Blacksmith Forge").
        """
        self.name = name
        self.station_type = station_type

    def interact(self, player: 'Character', screen):
        """Handle interaction with the crafting station."""
        menu_font = pygame.font.Font(None, 36)
        title_font = pygame.font.Font(None, 48)
        running_crafting = True
        selected_recipe = 0

        while running_crafting:
            # Fill the screen for the crafting menu
            screen.fill(WHITE)
            logger.render(10, SCREEN_HEIGHT - 200)
            # Render crafting station title
            title_text = title_font.render(f"{self.name}", True, BLACK)
            screen.blit(title_text, (50, 50))

            # Render available recipes
            y_offset = 150
            possible_recipes = [j for j in player.inventory.known_recipes if j.required_station == self.station_type]
            for i, recipe in enumerate(possible_recipes):
                color = BLACK if i != selected_recipe else RED
                recipe_text = menu_font.render(
                    f"{recipe.name} - Requires: {', '.join([': '.join([ingredient[0].name, str(ingredient[1])]) for ingredient in recipe.ingredients])}", True, color
                )
                screen.blit(recipe_text, (50, y_offset))
                y_offset += 40

            pygame.display.flip()

            # Handle input for crafting menu
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    exit()
                elif event.type == KEYDOWN:
                    if event.key == K_DOWN:
                        selected_recipe = (selected_recipe + 1) % len(possible_recipes)
                    elif event.key == K_UP:
                        selected_recipe = (selected_recipe - 1) % len(possible_recipes)
                    elif event.key == K_RIGHT:  # Craft selected recipe
                        print(f"Crafting {possible_recipes[selected_recipe].name}...")
                        recipe = possible_recipes[selected_recipe]
                        player.inventory.craft(recipe, player)
                    elif event.key == K_ESCAPE:  # Exit the crafting menu
                        running_crafting = False


class Companion: # A companion is a non-player character that can assist the player in combat
    def __init__(self, name: str, companion_class: str, health: float, damage: float, skills: list['Skill']):
        self.name = name
        self.companion_class = companion_class
        self.health = health
        self.damage = damage
        self.skills = skills

    def assist(self, target):
        """Companion assists the player in combat."""
        print(f"{self.name} assists by dealing {self.damage} damage to {target.name}!")
        target.take_damage(self.damage)

    def use_skill(self, skill: 'Skill', target=None):
        """Use one of the companion's abilities."""
        if skill in self.skills:
            print(f"{self.name} uses {skill}!")
            # Define specific skill effects here
            if skill == "Heal":
                print(f"{self.name} heals their ally!")
            elif target:
                print(f"{self.name} attacks {target.name} with {skill}!")
        else:
            print(f"{self.name} doesn't have the skill '{skill}'.")


class City:
    def __init__(self, name, population, guards, faction, shops, crafting_stations, x, y):
        self.name = name
        self.population = population
        self.guards = guards
        self.faction = faction
        self.shops = shops  # List of Shop objects
        self.crafting_stations = crafting_stations  # List of CraftingStation objects
        self.x = x
        self.y = y
        self.color = (0, 0, 0)  # Black color for the city
    def enter(self, player, screen):
        """Handle entering the city and showing the menu."""
        running_city = True
        menu_font = pygame.font.Font(None, 36)
        title_font = pygame.font.Font(None, 48)
        selected_option = 0
        options = ["Visit Shop", "Use Crafting Station", "Talk to Locals", "Leave"]

        while running_city:
            # Fill screen with city background
            screen.fill(WHITE)
            logger.render(10, SCREEN_HEIGHT - 200)
            # Render city title
            title_text = title_font.render(f"Welcome to {self.name}", True, BLACK)
            screen.blit(title_text, (50, 50))

            # Render city menu options
            y_offset = 150
            for i, option in enumerate(options):
                color = BLACK if i != selected_option else RED
                option_text = menu_font.render(option, True, color)
                screen.blit(option_text, (50, y_offset))
                y_offset += 40

            pygame.display.flip()

            # Handle city menu input
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    exit()
                elif event.type == KEYDOWN:
                    if event.key == K_DOWN:
                        selected_option = (selected_option + 1) % len(options)
                    elif event.key == K_UP:
                        selected_option = (selected_option - 1) % len(options)
                    elif event.key == K_RETURN:  # Select an option
                        if selected_option == 0:  # Visit shop
                            for shop in self.shops:
                                render_shop_menu(screen, shop, player)
                        elif selected_option == 1:  # Use crafting station
                            self.visit_crafting_station(player, screen)
                        elif selected_option == 2:  # Talk to locals
                            print("You chat with the locals and learn about the city.")
                        elif selected_option == 3:  # Leave the city
                            running_city = False

    def draw(self, screen):
        """Draw the city on the screen."""
        pygame.draw.rect(screen, self.color, (self.x, self.y, 35, 35))  # City marker
        font = pygame.font.Font(None, 24)
        text = font.render(self.name, True, (0, 0, 0))
        screen.blit(text, (self.x - 5, self.y - 23))

    def visit_crafting_station(self, player, screen):
        """Visit a crafting station in the city."""
        menu_font = pygame.font.Font(None, 36)
        selected_station = 0
        running_menu = True

        while running_menu:
            # Render crafting stations menu
            screen.fill(WHITE)
            logger.render(10, SCREEN_HEIGHT - 200)
            y_offset = 100
            for i, station in enumerate(self.crafting_stations):
                color = BLACK if i != selected_station else RED
                station_text = menu_font.render(f"{station.name} ({station.station_type})", True, color)
                screen.blit(station_text, (50, y_offset))
                y_offset += 40
            pygame.display.flip()

            # Handle menu input
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    exit()
                elif event.type == KEYDOWN:
                    if event.key == K_DOWN:
                        selected_station = (selected_station + 1) % len(self.crafting_stations)
                    elif event.key == K_UP:
                        selected_station = (selected_station - 1) % len(self.crafting_stations)
                    elif event.key == K_RETURN:  # Select crafting station
                        self.crafting_stations[selected_station].interact(player, screen)
                        running_menu = False
                    elif event.key == K_ESCAPE:  # Exit crafting menu
                        running_menu = False
    
    def draw_at(self, screen, position):
        """Draw the character at a specific screen position."""
        pygame.draw.rect(screen, self.color, (*position, 30, 30))
        font = pygame.font.Font(None, 24)
        text = font.render(self.name, True, BLACK)
        screen.blit(text, (position[0], position[1] - 15))

class Recipe:
    def __init__(self, name: str, ingredients: list[tuple[Item, int]], result: Item, required_station: str, experience: int):
        self.name = name
        self.ingredients = ingredients
        self.result = result
        self.required_station = required_station
        self.experience = experience

class Inventory:
    def __init__(self, player: 'Character'=None, name: str='Inventory', capacity: int=20, contents: list[tuple[Item, int]]=[], known_recipes: list[Recipe]=[]):
        self.name = name
        self.player = player
        self.capacity = capacity
        self.contents = contents
        self.known_recipes = known_recipes

    def add_recipe(self, recipe: Recipe):
        """Discover a new crafting recipe."""
        if recipe not in self.known_recipes:
            self.known_recipes.append(recipe)
            print(f'New recipe discovered: {recipe.result.name}')
            print()
        else:
            print(f'Recipe for {recipe.result.name} already known.')
            print()
    # def check_crafting_requirements(self, requirements: dict, player: 'Character') -> bool:
    #     """Check if the player meets the requirements to craft an item."""
    #     for stat, value in requirements.items():
    #         if stat == "character_class" and player.character_class != value:
    #             print(f"Cannot craft this item. Requires {value} class. You are a {player.character_class}.")
    #             return False
    #         elif stat == "crafting_level" and player.crafting_level < value:
    #             print(f"Cannot craft this item. Requires crafting level {value}. Current: {player.crafting_level}.")
    #             return False
    #         elif stat in vars(player) and getattr(player, stat, 0) < value:
    #             print(f"Cannot craft this item. Requires {stat} >= {value}. Current: {getattr(player, stat, 0)}.")
    #             return False
    #     return True

    def calculate_crafted_quality(self, recipe: tuple) -> str:
        """Calculate the quality of the crafted item based on the materials used."""
        # material_quality = [item[0].quality for item in self.contents if item in recipe]
        # if all(q == "Legendary" for q in material_quality):
        #     return "Legendary"
        # elif all(q in ("Epic", "Legendary") for q in material_quality):
        #     return "Epic"
        # elif all(q in ("Rare", "Epic", "Legendary") for q in material_quality):
        #     return "Rare" if any(q == "Rare" for q in material_quality) else "Epic"
        # return "Common"
        return "Crafted"

    def craft(self, recipe: Recipe, player: 'Character'):
        """Craft an item using the given recipe."""

        # Retrieve recipe details
        required_resources = recipe.ingredients
        result_item = recipe.result
        crafting_experience = recipe.experience

        # Check crafting station
        # if required_station and station != required_station:
        #     print(f"This recipe requires a {required_station}. You are using a {station}.")
        #     return

        # Validate crafting requirements (stats, level, class, etc.)
        # if not self.check_crafting_requirements(crafting_requirements, player):
        #     return

        # Validate required resources

        for material, count in required_resources:
            if material not in [i[0] for i in self.contents] or self.contents[[i[0] for i in self.contents].index(material)][1] < count:
                print("You lack the necessary resources to craft this item.")
                return

        # Calculate result item quality based on material quality
        crafted_quality = self.calculate_crafted_quality(required_resources)
        result_item.quality = crafted_quality
        if self.capacity >= len(self.contents) + 1: # Check if inventory has space
            # Remove used resources from inventory
            for material, count in required_resources:
                for item in range(len([self.contents])):
                    if self.contents[item] == material:
                        self.contents[item][-1] -= count
                        if self.contents[item][-1] == 0:
                            del self.contents[item]
                            break
            # Add crafted item to inventory
            self.add_item(result_item)
            print(f"Crafted a {crafted_quality} {result_item.name}!")
            player.gain_crafting_experience(crafting_experience)
        else:
            print("Inventory is full. Cannot craft this item.")
            print()

    def add_item(self, item: Item, count: int = 1):
        """Add an item to the inventory."""
        if self.capacity >= len(self.contents) + 1 or item.name in [i[0].name for i in self.contents]:
            if item.name in [i[0].name for i in self.contents]:
                for i in range(len(self.contents)):
                    if self.contents[i][0].name == item.name:
                        self.contents[i][1] += count
                        break
            else:
                self.contents.append([item, count])
            print(f'Added {item.name} x {count} to inventory.')
            item.trigger_quest(self.player)
        else:
            print(f'Inventory is full. Cannot add {item.name}.')
            print()
    def display_recipes(self):
        """Display all known recipes."""
        print("Known Recipes:")
        for recipe in self.known_recipes:
            ingredients = ", ".join([f"{item} x{qty}" for item, qty in recipe.ingredients.items()])
            print(f" - {recipe.name}: {ingredients} -> {recipe.result.name}")


    def remove_item(self, item: Item):
        """
        Remove an item from the inventory.
        :param item: The item to remove.
        """
        for idx, (inv_item, quantity) in enumerate(self.contents):
            if inv_item.name == item.name:
                if quantity > 1:
                    self.contents[idx][1] -= 1
                else:
                    self.contents.pop(idx)
                print(f"Removed {item.name} from inventory.")
                return
        print(f"{item.name} not found in inventory.")
        
    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self._index < len(self.contents):
            item = self.contents[self._index]
            self._index += 1
            return item
        else:
            raise StopIteration
    def __len__(self):
        return len(self.contents)

class Character: # Player
    def __init__(self, name: str, inventory: Inventory, character_class: str, max_health: float=100.0, strength: float=10.0, intelligence: float=10.0, agility: float=10.0, luck: float=10.0,  experience: float=0.0, level: int=1, saturation: float=10.0, max_mana: float=15.0, quests: list[Quest]=[], reputation: dict['Faction': int]={}, completed_quests: list[Quest]=[], city: City=None, race: str='Human', special_abilities: list[str]=[], achievements: list[str]=[], skills: list['Skill']=[], crafting_level: int = 1, crafting_experience: float = 0, gold: int = 100, x: float=400, y: float=300, faction_reputation: dict[str, int]={}, faction: 'Faction' = None):
        self.x = x
        self.y = y
        self.color = GREEN
        self.skills = skills
        self.achievements = achievements
        self.name = name
        self.race = race
        self.max_health = max_health
        self.inventory = inventory
        self.character_class = character_class
        self.strength = strength
        self.intelligence = intelligence
        self.agility = agility
        self.luck = luck
        self.experience = experience
        self.level = level
        self.right_hand = None
        self.left_hand = None
        self.armor_chest = None
        self.armor_head = None
        self.armor_legs = None
        self.armor_feet = None
        self.defense = 10.0
        self.damage = 5.0
        self.faction = faction
        self.faction_reputation = faction_reputation
        self.city = city
        self.respawn_time = 10
        self.reputation = reputation
        self.completed_quests = completed_quests
        self.active_quest = None
        self.saturation = saturation
        self.special_abilities = special_abilities
        self.health = self.max_health
        self.max_saturation = 10.0
        self.max_mana = max_mana * 5 if character_class == 'Mage' else max_mana * 3 if character_class == 'Shaman' else max_mana * 0.75 if character_class == 'Rogue' else max_mana
        self.mana = self.max_mana
        self.quests = quests
        self.alive = True
        self.crafting_level = crafting_level
        self.crafting_experience = crafting_experience
        self.gold = gold
        self.resting = False
    def move(self, keys):
        """Move the character using the arrow keys."""
        if keys[K_UP]:
            self.y -= 5
        if keys[K_DOWN]:
            self.y += 5
        if keys[K_LEFT]:
            self.x -= 5
        if keys[K_RIGHT]:
            self.x += 5
    
    def collect_resource(self, resource: 'Resource'):
        """Collect a resource and add it to the player's inventory."""
        print(f"{self.name} collected {resource.resource_type}.")
        self.inventory.add_item(Item(name=resource.resource_type, quality=resource.quality), resource.quantity)
        resource.collected = True
        threading.Thread(target=resource.respawn).start()

    def draw(self, screen):
        """Draw the character on the screen."""
        if self.alive:
            pygame.draw.rect(screen, self.color, (self.x, self.y, 30, 30))
            font = pygame.font.Font(None, 24)
            text = font.render(self.name, True, (0, 0, 0))
            screen.blit(text, (self.x, self.y - 15))
    def adjust_reputation(self, faction: 'Faction', amount: int):
        """
        Adjust the player's reputation with a specific faction.
        :param faction: The faction object.
        :param amount: The amount to adjust reputation by (positive or negative).
        """
        if faction.name not in self.faction_reputation:
            self.faction_reputation[faction.name] = faction.base_reputation

        self.faction_reputation[faction.name] += amount
        print(f"Reputation with {faction.name} is now {self.faction_reputation[faction.name]} ({self.get_reputation_tier(faction)}).")

    def get_reputation_tier(self, faction: 'Faction') -> str:
        """
        Get the player's reputation tier with a faction.
        :param faction: The faction object.
        :return: The reputation tier (e.g., 'Hostile', 'Neutral', 'Friendly').
        """
        reputation = self.faction_reputation.get(faction.name, faction.base_reputation)
        if reputation < -50:
            return "Hostile"
        elif -50 <= reputation < 0:
            return "Unfriendly"
        elif 0 <= reputation < 50:
            return "Neutral"
        elif 50 <= reputation < 100:
            return "Friendly"
        else:
            return "Honored"

    def gain_crafting_experience(self, exp: float):
        """"Gain crafting experience."""
        self.crafting_experience += exp
        print(f"{self.name} gained {exp} crafting experience.")
        if self.crafting_experience >= self.crafting_level * 100:
            self.level_up_crafting()
            return
        print()
    def accept_quest(self, quest: Quest):
        """Accept a quest."""
        if quest in self.quests or quest in self.completed_quests:
            print(f"Quest '{quest.name}' is already accepted or completed.")
            return
        self.quests.append(quest)
        self.active_quest = quest
        print(f"Quest '{quest.name}' accepted.")

    def complete_quest(self, quest: Quest):
        """Complete a quest."""
        quest.completed = True
        if quest in self.quests:
            self.quests.remove(quest)
            self.completed_quests.append(quest)
            print(f"Quest '{quest.name}' marked as completed!")
            if self.inventory.capacity - len(self.inventory.contents) >= len(quest.rewards):
                quest.give_rewards(self)
            else:
                print("Not enough space in inventory to receive quest rewards. Clear some space and come to the quest giver to receive rewards.")
                quest.completed = True
        else:
            print(f"Quest '{quest.name}' cannot be marked complete.")

    def level_up_crafting(self):
        """Level up in crafting."""
        self.crafting_level += 1
        self.crafting_experience = 0
        print(f"{self.name} leveled up in crafting to level {self.crafting_level}!")
        print()
    def bind_skill(self, skill: 'Skill', key: int=1):
        """Bind a skill to a key."""
        if skill in self.skills:
            self.skills.insert(key - 1, self.skills.pop(self.skills.index(skill)))
            return
        print(f"Skill '{skill.name}' is not found.")

    def equip_weapon(self, weapon: Weapon, hand: str = 'right'):
        """Equip a weapon."""
        if not self.check_requirements(weapon):
            return
        if weapon.character_class != self.character_class:
            print(f"{weapon.name} cannot be equipped by a {self.character_class}. Required: {weapon.character_class}.")
            print()
            return
        if weapon in [i[0] for i in self.inventory.contents]:
            if hand == 'right':
                if self.right_hand:
                    self.unequip_weapon(self.right_hand)
                self.right_hand = weapon
                self.damage += weapon.damage
                print(f"{weapon.name} equipped in right hand. Your damage: {self.damage}")
            elif hand == 'left':
                if self.left_hand:
                    self.unequip_weapon(self.left_hand)
                self.left_hand = weapon
                self.damage += weapon.damage
                print(f"{weapon.name} equipped in left hand. Your damage: {self.damage}")
        else:
            print('Weapon not in inventory')
            print()
    def check_requirements(self, item: Item) -> bool:
        """Check if the player meets the requirements to use the item."""
        if not item.requirements:
            return True
        for stat, required_value in item.requirements.items():
            if getattr(self, stat, 0) < required_value:
                print(f"Cannot use {item.name}. Requires {stat} {required_value}. Current: {getattr(self, stat, 0)}.")
                print()
                return False
        return True

    def increase_reputation(self, faction: str, amount: int):
        """Increase reputation with a faction."""
        if faction not in self.reputation:
            self.reputation[faction] = 0
        self.reputation[faction] += amount
        print(f'Reputation with {faction} increased by {amount}.')
        print()
    
    def decrease_reputation(self, faction: str, amount: int):
        """Decrease reputation with a faction."""
        if faction not in self.reputation:
            self.reputation[faction] = 0
        self.reputation[faction] -= amount
        print(f'Reputation with {faction} decreased by {amount}.')
        print()
    
    def get_reputation(self, faction: str):
        """Get reputation with a faction."""
        return self.reputation.get(faction, 0)

    def unequip_weapon(self, weapon: Weapon):
        """unequip a weapon."""
        if weapon in [i[0] for i in self.inventory.contents]:
            if self.right_hand == weapon:
                self.right_hand = None
                self.damage -= weapon.damage
                print(f"{weapon.name} unequipped from right hand.")
            elif self.left_hand == weapon:
                self.left_hand = None
                print(f"{weapon.name} unequipped from left hand.")
                self.damage -= weapon.damage
            else:
                print('Weapon not equipped')
                print()
        else:
            print('Weapon not in inventory')
            print()
    def learn_skill(self, skill: str, cost: int, skill_type: str, value: int):
        """Learn a skill."""
        if skill in self.skills:
            print(f'{self.name} already knows {skill}')
            print()
        else:
            self.skills[skill] = [cost, skill_type, value]
            print(f'{self.name} learned {skill}') 
            print()
    def use_skill(self, skill: 'Skill', target: 'Mob'):
        """Use a skill."""
        if skill in self.skills:
            if self.mana >= skill.cost:
                self.mana -= skill.cost
                if skill.skill_type == 'heal':
                    target.health += skill.value
                    if target.health > target.max_health:
                        target.health = target.max_health
                    print(f'{self.name} used {skill.name} on {target.name} and healed them for {skill.value} health')
                    print()
                elif skill.skill_type == 'damage':
                    print(f'{self.name} used {skill.name} on {target.name}.')
                    target.take_damage(skill.value, self)
                    print()
                elif skill.skill_type == 'defense':
                    self.defense += skill.value
                    print(f'{self.name} used {skill.name} and increased their defense by {skill.value}')
                    print()
            else:
                print(f'{self.name} does not have enough mana to use {skill.name} (needs {skill.cost} mana)')
                print()
        else:
            print(f'{self.name} does not know {skill.name} skill.')
            print()
    def equip_armor(self, armor: Armor):
        """Equip an armor."""
        if not self.check_requirements(armor):
            return
        if armor.character_class != self.character_class:
            print(f"{armor.name} cannot be equipped by a {self.character_class}. Required: {armor.character_class}.")
            print()
            return
        if armor in [i[0] for i in self.inventory.contents]:
            if armor.slot == 'chest':
                self.armor_chest = armor
                if self.armor_chest and self.armor_chest != armor:
                    self.unequip_armor(self.armor_chest)
                self.defense += armor.defense
                if self.health == self.max_health:
                    self.health += armor.health
                self.max_health += armor.health
                self.strength += armor.strength
                self.agility += armor.agility
                print(f'{armor.name} equipped')
                print()
            elif armor.slot == 'head':
                if self.armor_head and self.armor_head != armor:
                    self.unequip_armor(self.armor_head)
                self.armor_head = armor
                self.defense += armor.defense
                if self.health == self.max_health:
                    self.health += armor.health
                self.max_health += armor.health
                self.strength += armor.strength
                self.agility += armor.agility
                print(f'{armor.name} equipped')
                print()
            elif armor.slot == 'legs':
                if self.armor_legs and self.armor_legs != armor:
                    self.unequip_armor(self.armor_legs)
                self.armor_legs = armor
                self.defense += armor.defense
                if self.health == self.max_health:
                    self.health += armor.health
                self.max_health += armor.health
                self.strength += armor.strength
                self.agility += armor.agility
                print(f'{armor.name} equipped')
                print()
            elif armor.slot == 'feet':
                if self.armor_feet and self.armor_feet != armor:
                    self.unequip_armor(self.armor_feet)
                self.armor_feet = armor
                self.defense += armor.defense
                if self.health == self.max_health:
                    self.health += armor.health
                self.max_health += armor.health
                self.strength += armor.strength
                self.agility += armor.agility
                print(f'{armor.name} equipped')
                print()
            else:
                print('Invalid armor slot')
                print()
        else:
            print('Armor not in inventory')
            print()
    def to_city(self, city: City):
        """Travel to a city."""
        if self.city == city:
            print(f'{self.name} is already in the city {city.name}')
            print()
        else:
            self.city = city
            print(f'{self.name} is now in the city {city.name}')
            print()
    def display_inventory(self):
        """Display the player's inventory."""
        print("Your Inventory:")
        for item in [i[0] for i in self.inventory.contents]:
            print(f" - {item.name}")
        print(f"Gold: {self.gold}")

    def unequip_armor(self, armor: Armor):
        """unequip an armor."""
        if armor in [i[0] for i in self.inventory.contents]:
            if armor.character_class == self.character_class:
                if self.armor_chest == armor:
                    self.armor_chest = None
                    self.defense -= armor.defense
                    if self.health == self.max_health:
                        self.health -= armor.health
                    self.max_health -= armor.health
                    self.strength -= armor.strength
                    self.agility -= armor.agility
                    print(f'{armor.name} unequipped')
                    print()
                elif self.armor_head == armor:
                    self.armor_head = None
                    self.defense -= armor.defense
                    if self.health == self.max_health:
                        self.health -= armor.health
                    self.max_health -= armor.health
                    self.strength -= armor.strength
                    self.agility -= armor.agility
                    print(f'{armor.name} unequipped')
                    print()
                elif self.armor_legs == armor:
                    self.armor_legs = None
                    self.defense -= armor.defense
                    if self.health == self.max_health:
                        self.health -= armor.health
                    self.max_health -= armor.health
                    self.strength -= armor.strength
                    self.agility -= armor.agility
                    print(f'{armor.name} unequipped')
                    print()
                elif self.armor_feet == armor:
                    self.armor_feet = None
                    self.defense -= armor.defense
                    if self.health == self.max_health:
                        self.health -= armor.health
                    self.max_health -= armor.health
                    self.strength -= armor.strength
                    self.agility -= armor.agility
                    print(f'{armor.name} unequipped')
                    print()
                else:
                    print('Armor not equipped')
                    print()
    def attack(self, target: 'Mob'):
        """Attack a target."""
        is_critical = randint(1, 100) <= self.luck
        damage = self.damage * (2 if is_critical else 1)
        if self.character_class == 'Warrior' or self.character_class == 'Paladin' or self.character_class == 'Rogue' or self.character_class == 'Berserker' or self.character_class == 'Knight':
            damage += round(damage * self.strength / 100, 2)
        elif self.character_class == 'Mage' or self.character_class == 'Sorcerer' or self.character_class == 'Wizard' or self.character_class == 'Necromancer':
            damage += round(damage * self.intelligence / 100, 2)
        else:
            damage += round(damage * self.agility / 100, 2)
        print(f'{self.name} attacks {target.name}')
        target.take_damage(damage, attacker=self)

        if self.right_hand:
            self.right_hand.durskill -= 1
            if self.right_hand.durskill <= 0:
                print(f"{self.right_hand.name} has broken!")
                if not self.left_hand:
                    print()
                self.inventory.remove_item(self.right_hand)
                self.unequip_weapon(self.right_hand)
        if self.left_hand:
            self.left_hand.durskill -= 1
            if self.left_hand.durskill <= 0:
                print(f"{self.left_hand.name} has broken!")
                print()
                self.inventory.remove_item(self.left_hand)
                self.unequip_weapon(self.left_hand)

        self.saturation -= 0.5
    def consume(self, item: Item):
        """Consume an item."""
        if not self.check_requirements(item):
            return
        if item in [i[0] for i in self.inventory.contents]:
            try:
                if item.item_type == 'Potion': # potion is a separate class but depends on Item
                    if item.potion_type == 'Heal':
                        self.health += item.value
                    elif item.potion_type == 'Strength':
                        self.strength += item.value
                    elif item.potion_type == 'Agility':
                        self.agility += item.value
                    elif item.potion_type == 'Defense':
                        self.defense += item.value
                    elif item.potion_type == 'Mana':
                        self.mana += item.value
                    else:
                        print('Invalid potion type')
                        return
                    if self.health > self.max_health:
                        self.health = self.max_health
                    if self.mana > self.max_mana:
                        self.mana = self.max_mana
                    print(f'{self.name} consumed {item.name} ({item.potion_type}). Health: {self.health}, Mana: {self.mana}')
                    for i in range(len(self.inventory.contents)):
                        if self.inventory.contents[i][0] == item:
                            self.inventory.contents[i][1] -= 1
                            if self.inventory.contents[i][1] == 0:
                                del self.inventory.contents[i]
                            break
                    print()
                elif item.item_type == 'Food':
                    self.saturation += item.saturation
                    self.health += item.health
                    if self.health > self.max_health:
                        self.health = self.max_health
                    if self.saturation > self.max_saturation:
                        self.saturation = self.max_saturation
                    print(f'{self.name} consumed {item.name}. Health: {self.health}, saturation: {self.saturation}')
                    print()
            except AttributeError:
                print('Consume: Invalid item')
        else:
            print(f'{item.name} not found in inventory.')
            print()
    # def use_item(self, item: Item):
    #     """Use an item."""
    #     if item in [i[0] for i in self.inventory.contents]:
    #         if issubclass(item, Weapon):
    #             self.equip_weapon(item)
    #         elif issubclass(item, Armor):
    #             self.equip_armor(item, item.slot)
    #         elif issubclass(item, Potion) or issubclass(item, Food):
    #             self.consume(item)
    #     else:
    #         print('Item not in inventory')
            print()
    def take_damage(self, damage: float) -> bool:
        """Take damage."""
        __agility = randint(30, 100)
        if self.right_hand is not None:
            __shield = randint(0, 10) if self.right_hand.weapon_type == 'Shield' else 11
        else:
            __shield = 11
        if self.agility > __agility or __shield < 1:
            print(f'{self.name} dodged the attack' if self.agility > __agility else f'{self.name} blocked the attack')
            print()
        else:
            if self.defense > 95:
                self.defense = 95
            damage = round(damage * (1 - self.defense / 100), 2)
            self.health -= damage
            print(f'{self.name} took {damage} damage')
            print(f'{self.name} has {self.health if self.health >= 0 else 0} health left')
            if self.health > 0:
                print()
        if self.health <= 0:
                print(f'{self.name} died')
                print()
                self.die()
                logger.render(10, SCREEN_HEIGHT - 200)
                return True
        self.saturation -= 0.5
    def die(self):
        """Die and respawn after a delay."""
        if not self.alive:  # Prevent repeated calls
            return
        self.health = 0
        self.alive = False
        print(f"{self.name} is dead and will respawn in {self.respawn_time} seconds.")
        lost_experience = self.level * 10
        print(f"{self.name} lost {lost_experience} experience upon death.")
        self.experience -= lost_experience
        if self.experience < 0:
            if self.level > 1:
                self.level -= 1
                self.experience = self.level * 100 - min(abs(self.experience), self.level * 100)
            else:
                self.level = 1
                self.experience = 0
        threading.Thread(target=self.respawn_after_delay).start()
        logger.render(10, SCREEN_HEIGHT - 200)

    def respawn_after_delay(self):
        """Call respawn after a delay"""
        sleep(self.respawn_time); self.respawn()
    def respawn(self):
        """Respawn."""
        self.health = self.max_health
        self.mana = self.max_mana
        self.saturation = 10
        self.alive = True
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        print(f"{self.name} has respawned.")
        print()
    def regenerate(self, seconds: int, health_rate: float=1, mana_rate: float=1):
        """Regenerate health and mana."""
        self.resting = True
        for _ in range(seconds):
            sleep(1)
            if self.health < self.max_health:
                self.health += health_rate
                if self.health > self.max_health:
                    self.health = self.max_health
            if self.mana < self.max_mana:
                self.mana += mana_rate
                if self.mana > self.max_mana:
                    self.mana = self.max_mana
        self.resting = False


    def gain_experience(self, exp_amount):
        """Gain experience."""
        self.experience += exp_amount
        print(f'{self.name} gained {exp_amount} experience')
        if self.experience >= self.level * 100:
            self.level_up()

    def level_up(self):
        """Level up."""
        self.level += 1
        self.strength += 2
        self.health += 10
        self.mana += 5
        self.max_health += 10
        self.max_mana += 5
        if self.agility > 95:
            self.agility = 95
        print(f'{self.name} leveled up to level {self.level}!')
        self.experience = self.experience - (self.level * 100)
        if self.experience < 0:
            self.experience = 0
        if self.experience > self.level * 100:
            self.level_up()
            return
        print()
        
    def rest(self, seconds: int):
        """Rest for a number of seconds and regenerate health and mana."""
        threading.Thread(target=self.regenerate, args=(seconds, )).start()
        print(f'{self.name} rested for {seconds} seconds.')
        print(f'{self.name} has {self.health} health and {self.mana} mana.')
        print()
    def unlock_achievement(self, achievement_name: str):
        """Unlock an achievement."""
        if achievement_name not in self.achievements:
            self.achievements.append(achievement_name)
            print(f"Achievement unlocked: {achievement_name}")
            print()

    def draw_at(self, screen, position):
        """Draw the character at a specific screen position."""
        pygame.draw.rect(screen, self.color, (*position, 30, 30))
        font = pygame.font.Font(None, 24)
        text = font.render(self.name, True, BLACK)
        screen.blit(text, (position[0], position[1] - 15))

class Skill: # To not store skills in a tuple because it is inconvenient to use.
    def __init__(self, name: str, skill_type: str, value: float, cost: float):
        self.name = name
        self.skill_type = skill_type
        self.value = value
        self.cost = cost
    def level_up(self):
        """Level up."""
        self.value += 3
        self.cost += 2

class Mob: # Anything that can be killed.
    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        health: float = 100.0,
        max_health: float = 100.0,
        damage: float = 10.0,
        strength: float = 10.0,
        level: int = 1,
        mana: float = 100.0,
        max_mana: float = 100.0,
        defense: float = 10.0,
        evil: bool = True,
        mob_class: str = 'Warrior',
        race: str = 'Goblin',
        gender: str = 'Male',
        experience: float = 0.0,
        alive: bool = True,
        mob_type: str = 'Monster',
        skills: dict = None,
        loot: Item = None,
        trigger: Quest = None, # Quest that triggers the mob
        is_boss: bool = False,
    ):
        self.name = name
        self.health = health
        self.max_health = max_health
        self.damage = damage
        self.strength = strength
        self.level = level
        self.mana = mana
        self.max_mana = max_mana
        self.defense = defense
        self.evil = evil
        self.mob_class = mob_class
        self.race = race
        self.gender = gender
        self.experience = experience
        self.alive = alive
        self.mob_type = mob_type
        self.skills = skills if skills is not None else {}
        self.loot = loot
        self.trigger = trigger
        self.is_boss = is_boss
        self.color = RED if self.evil else BLUE
        self.x = x
        self.y = y

    def __str__(self):
        return f'Mob {self.name} with health {self.health} and damage {self.damage}'
    
    def draw(self, screen):
        if self.alive:
            pygame.draw.rect(screen, self.color, (self.x, self.y, 30, 30))
            font = pygame.font.Font(None, 24)
            text = font.render(self.name, True, (0, 0, 0))
            screen.blit(text, (self.x, self.y - 15))

    def migrate(self):
        self.x, self.y = random.randint(0, 800), random.randint(0, 600)  # New position


    def take_damage(self, damage: float, attacker: 'Character'):
        """Take damage."""
        if not self.alive:
            print(f"{self.name} is already dead.")
            return

        self.health -= damage
        print(f"{self.name} took {damage} damage. Remaining health: {max(self.health, 0)}.")

        if self.health <= 0:
            self.alive = False
            print(f"{self.name} has been slain!") 
            if self.loot:
                print(f"{self.name} dropped {self.loot.name}.")
                if attacker.inventory.capacity - len(attacker.inventory.contents) >= 1:
                    attacker.inventory.add_item(self.loot)
                    print(f'You have gained {self.loot.name}!')
                else:
                    print(f'ou have no room in your inventory for {self.loot.name}')       
            if self.trigger: # Grant reward if available
                    attacker.complete_quest(self.trigger)
            # Grant experience
            attacker.gain_experience(self.experience)
            threading.Timer(10, self.respawn).start()  
            return
        self.attack(attacker)
    def attack(self, target: 'Character'):
        """Attack a target."""
        if self.alive:
            print(f'{self.name} attacks {target.name}')
            target.take_damage(self.damage)
            if not target.alive:
                self.health = self.max_health
                self.mana = self.max_mana
    def respawn(self):
        """Respawn the mob after a delay."""
        self.health = self.max_health
        self.alive = True
        print(f"{self.name} has respawned!")


    def use_skill(self, target: 'Character'):
        """Use a skill."""
        if self.alive:
            if self.health < self.max_health / 2:
                for i in self.skills:
                    if self.skills[i].skill_type == 'Heal':
                        self.health += self.skills[i].value
                        self.mana -= self.skills[i].cost
                        print(f'{self.name} used skill {i} and healed for {self.mana}')
                        print()
                        if self.health > self.max_health:
                            self.health = self.max_health
                        if self.mana < 0:
                            self.mana = 0
                        return
            else:
                for i in self.skills:
                    if self.skills[i].skill_type == 'Damage':
                        print(f'{self.name} used skill {i} on {target.name}')
                        target.take_damage(self.skills[i].value)
                        self.mana -= self.skills[i].cost
                        if self.mana < 0:
                            self.mana = 0
                        return

    def draw_at(self, screen, position):
        """Draw the mob at a specific screen position."""
        if self.alive:
            pygame.draw.rect(screen, self.color, (*position, 30, 30))
            font = pygame.font.Font(None, 24)
            text = font.render(self.name, True, BLACK)
            screen.blit(text, (position[0], position[1] - 15))


class WorldClock: # Do not used yet. Planning to add a day/night cycle with minor events.
    def __init__(self):
        self.day = 0
        self.time_of_day = "Morning"

    def advance_time(self):
        """Advance the time by one day."""
        self.day += 1
        if self.time_of_day == "Morning":
            self.time_of_day = "Afternoon"
        elif self.time_of_day == "Afternoon":
            self.time_of_day = "Evening"
        elif self.time_of_day == "Evening":
            self.time_of_day = "Night"
        else:
            self.time_of_day = "Morning"

    def print_day_info(self):
        """Print the current day and time of day."""
        print(f"Day {self.day}: {self.time_of_day}")
        print()

class NPC: # NPC with quests
    def __init__(self, name: str, quests: list[Quest], x: int, y: int):
        self.name = name
        self.quests = quests
        self.x = x
        self.y = y
        self.color = BLUE

    def interact(self, player: 'Character'):
        """Give a quest to the player."""
        for quest in self.quests:
            if quest in player.quests and quest.completed:
                player.complete_quest(quest)
            elif quest not in player.quests and quest not in player.completed_quests and quest.level <= player.level:
                player.accept_quest(quest)
                print(f"{self.name} has given the quest: '{quest.name}'.")
                return
        print(f"{self.name} has no quests available for {player.name}.")
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, 30, 30))
        font = pygame.font.Font(None, 24)
        text = font.render(self.name, True, (0, 0, 0))
        screen.blit(text, (self.x, self.y - 15))

    def draw_at(self, screen, position):
        """Draw the character at a specific screen position."""
        pygame.draw.rect(screen, self.color, (*position, 30, 30))
        font = pygame.font.Font(None, 24)
        text = font.render(self.name, True, BLACK)
        screen.blit(text, (position[0], position[1] - 15))

def display_notification(text, color, duration=2):
    """Display a temporary notification on the screen."""
    notification_font = pygame.font.Font(None, 36)
    notification = notification_font.render(text, True, color)
    screen.blit(notification, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
    pygame.display.flip()
    pygame.time.wait(int(duration * 1000))

def sleep(duration): # Useless but exists.
    """Pause the game for a specified duration."""
    time.sleep(duration)

def render_shop_menu(screen, shop: Shop, player: Character):
    """Render the shop menu and handle player interaction."""
    if shop.faction:
        tier = player.get_reputation_tier(shop.faction)
        if tier == "Hostile":
            print(f"The {shop.faction.name} refuses to trade with you.")
            return
        elif tier == "Unfriendly":
            print(f"The {shop.faction.name} imposes a 20% surcharge due to your poor reputation.")

        # Apply discounts or penalties based on reputation tier
        multiplier = 1.0
        if tier == "Friendly":
            multiplier = 0.9  # 10% discount
        elif tier == "Unfriendly":
            multiplier = 1.2  # 20% surcharge

        print(f"Welcome to {shop.name}!" + (f"Prices adjusted for your reputation ({tier}).") if shop.faction else "")
        for idx, item in enumerate(shop.items, start=1):
            adjusted_price = int(getattr(item, 'price', 0) * multiplier)
            print(f"{idx}. {item.name} - {adjusted_price} gold")

        # Buying logic remains unchanged, just apply adjusted prices
    menu_font = pygame.font.Font(None, 36)
    title_font = pygame.font.Font(None, 48)
    running_shop = True
    selected_item = 0  # Index of the currently selected item

    while running_shop:
        # Fill the screen for the shop menu
        screen.fill(WHITE)
        logger.render(10, SCREEN_HEIGHT - 200)
        # Render shop title
        title_text = title_font.render(f"Welcome to {shop.name}", True, BLACK)
        screen.blit(title_text, (50, 50))

        # Render shop items
        y_offset = 150
        for i, item in enumerate(shop.items):
            color = BLACK if i != selected_item else RED  # Highlight selected item
            item_text = menu_font.render(
                f"{item.name} - {item.quality} - {item.price * multiplier} Gold", True, color
            )
            screen.blit(item_text, (50, y_offset))
            y_offset += 40

        # Render player's gold
        gold_text = menu_font.render(f"Your Gold: {player.gold}", True, BLACK)
        screen.blit(gold_text, (50, y_offset + 20))

        pygame.display.flip()

        # Handle input for the shop menu
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()
            elif event.type == KEYDOWN:
                if event.key == K_DOWN:
                    selected_item = (selected_item + 1) % len(shop.items)  # Navigate down
                elif event.key == K_UP:
                    selected_item = (selected_item - 1) % len(shop.items)  # Navigate up
                elif event.key in [K_RETURN, K_RIGHT]:  # Buy selected item
                    item = shop.items[selected_item]
                    if player.gold >= item.price * multiplier:
                        player.gold -= item.price * multiplier
                        player.inventory.add_item(item)
                        print(f"You bought {item.name}!")
                    else:
                        print("Not enough gold!")
                elif event.key == K_ESCAPE:  # Exit the shop menu
                    running_shop = False

def render_inventory_menu(screen, player: Character, page: int = 1, items_per_page: int = 5):
    """
    Render the inventory on the Pygame screen with pagination and item interaction.
    """
    running_inventory = True
    selected_item = 0

    while running_inventory:
        # Clear screen
        screen.fill(WHITE)
        logger.render(10, SCREEN_HEIGHT - 200)
        # Inventory Header
        font = pygame.font.Font(None, 36)
        title = font.render(f"Inventory (Page {page})", True, BLACK)
        screen.blit(title, (20, 20))

        # Paginate items
        items, total_pages = paginate_list(player.inventory.contents, items_per_page, page)

        # Render items
        item_font = pygame.font.Font(None, 28)
        y_offset = 80
        for idx, (item, quantity) in enumerate(items):
            color = RED if idx == selected_item else BLACK
            item_text = f"{item.name} x{quantity}"
            text_surface = item_font.render(item_text, True, color)
            screen.blit(text_surface, (40, y_offset))
            y_offset += 40

        # Display navigation instructions
        nav_text = font.render(
            "[UP/DOWN to navigate, ENTER to use, Q to drop, LEFT to unequip, ESC to exit]",
            True,
            (128, 128, 128)
        )
        screen.blit(nav_text, (20, SCREEN_HEIGHT - 40))

        # Display page navigation
        page_nav_text = font.render(f"Page {page}/{total_pages}", True, (128, 128, 128))
        screen.blit(page_nav_text, (SCREEN_WIDTH - 150, 20))

        pygame.display.flip()

        # Event handling
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()
            elif event.type == KEYDOWN:
                if event.key == K_UP:  # Navigate up in the list
                    if len(player.inventory) > items_per_page:
                        if selected_item == 0:
                            page -= 1
                            if page == 0:
                                page = total_pages
                            selected_item = items_per_page - 1 if page != total_pages else len(player.inventory) % page
                        else:
                            selected_item = (selected_item - 1) % len(items)
                    else:
                        selected_item -= 1
                        if selected_item < 0:
                            selected_item = len(items) - 1
                elif event.key == K_DOWN:  # Navigate down in the list
                    if len(player.inventory) > items_per_page:
                        if selected_item == items_per_page - 1 or selected_item == len(player.inventory) % page and page == total_pages:
                            page += 1
                            if page > total_pages:
                                page = 1
                            selected_item = 0
                        else:
                            selected_item = (selected_item + 1) % len(items)
                    else:
                        selected_item += 1
                        if selected_item >= len(items):
                            selected_item = 0
                elif event.key == K_RETURN:  # Use selected item (Enter key)
                    if items:
                        item = items[selected_item][0]
                        if issubclass(item.__class__, Weapon):
                            player.equip_weapon(item)
                        elif issubclass(item.__class__, Armor):
                            player.equip_armor(item)
                        elif issubclass(item.__class__, Potion):
                            player.consume(item)
                        else:
                            print("Cannot use this item.")
                elif event.key == K_q:  # Drop selected item
                    if items:
                        item = items[selected_item][0]
                        player.inventory.remove_item(item)
                        print(f"Dropped {item.name}.")
                elif event.key == K_LEFT:  # Unequip selected item
                    if items:
                        item = items[selected_item][0]
                        if issubclass(item.__class__, Weapon):
                            player.unequip_weapon(item)
                        elif issubclass(item.__class__, Armor):
                            player.unequip_armor(item)
                        else:
                            print("Cannot unequip this item.")
                elif event.key == K_ESCAPE:  # Exit the inventory menu
                    running_inventory = False

def paginate_list(items: list, items_per_page: int, page: int):
    """
    Paginate a list into pages of a given size..
    """
    if not items:
        return [], 1  # Return an empty page if no items exist

    total_pages = (len(items) + items_per_page - 1) // items_per_page
    start = (page - 1) * items_per_page
    end = start + items_per_page
    paginated_items = items[start:end]
    return paginated_items, total_pages

class TextLogger:
    def __init__(self, screen, font, max_lines=6, line_height=20):
        self.screen = screen
        self.font = font
        self.max_lines = max_lines
        self.line_height = line_height
        self.logs = []

    def log(self, message, color=(0, 0, 0)):
        """Add a new message to the logs."""
        if len(self.logs) >= self.max_lines:
            self.logs.pop(0)  # Remove the oldest log if exceeding max_lines
        self.logs.append((message, color))

    def render(self, x, y, clear_background=False):
        """Render the text logs on the screen."""
        if clear_background:
            bg_width = self.screen.get_width()
            bg_height = self.line_height * self.max_lines
            pygame.draw.rect(self.screen, (255, 255, 255, 150), (x, y, bg_width, bg_height))  # Semi-transparent white

        for i, (log, color) in enumerate(self.logs):
            text_surface = self.font.render(log, True, color)
            self.screen.blit(text_surface, (x, y + i * self.line_height))

font = pygame.font.Font(None, 24)
logger = TextLogger(screen, font)
def display_print(*args, **kwargs):
    message = " ".join(map(str, args))
    color = kwargs.get("color", (0, 0, 0))  # Default color is black
    logger.log(message, color)  # Log the message in the TextLogger

# builtins.print = display_print

class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.offset_x = 0
        self.offset_y = 0

    def center_on(self, target):
        """Center the camera on the target (usually the player)."""
        self.offset_x = target.x - SCREEN_WIDTH // 2
        self.offset_y = target.y - SCREEN_HEIGHT // 2


    def apply(self, entity):
        screen_x = max(0, min(entity.x - self.offset_x, SCREEN_WIDTH))
        screen_y = max(0, min(entity.y - self.offset_y, SCREEN_HEIGHT))
        return screen_x, screen_y


class Resource:
    def __init__(self, x, y, resource_type, quality, quantity=1):
        self.x = x
        self.y = y
        self.resource_type = resource_type
        self.quality = quality
        self.respawn_time = 20
        self.collected = False
        self.quantity = quantity

    def respawn(self):
        """Respawn the resource after a delay."""
        sleep(self.respawn_time)
        self.collected = False


class GameWorld:
    def __init__(self, width, height, num_resources):
        self.width = width
        self.height = height
        self.resources = []
        self.generate_resources(num_resources)

    def generate_resources(self, num_resources):
        for _ in range(num_resources):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            resource_type = random.choice(["Iron Ore", "Herbs", "Wood", "Water", "Gold"])
            quantity = random.randint(1, 10)
            resource = Resource(x=x, y=y, resource_type=resource_type, quantity=quantity, quality='Common')
            self.resources.append(resource)

    def update_resources(self):
        """Update the state of all resources (respawning if needed)."""
        for resource in self.resources:
            resource.respawn()

    def draw_resources(self, screen, camera):
        for resource in self.resources:
            if not resource.collected:
                screen_x, screen_y = camera.apply(resource)
                print(f"Drawing resource at ({screen_x}, {screen_y})")  # Debug log
                pygame.draw.circle(screen, (0, 255, 0), (screen_x, screen_y), 10)



    def interact_with_resource(self, player_x, player_y, inventory):
        """Allow the player to collect resources if they're nearby."""
        for resource in self.resources:
            if not resource.collected and abs(player_x - resource.x) < 10 and abs(player_y - resource.y) < 10:
                resource.collect()
                inventory.add_item(Item(resource.type), resource.quantity)







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






GRAY = (128, 128, 128)

# Drawing logic for the main game screen
def draw_screen(screen, player, mobs, npcs, cities, camera, font, world):
    """Draw all game entities on the main screen."""
    # Fill the background
    screen.fill(WHITE)
    logger.render(10, SCREEN_HEIGHT - 200)
    # Draw the world (e.g., regions)
    world.draw(screen, camera)

    # Draw player
    if player.alive:
        player_screen_pos = camera.apply(player)
        player.draw_at(screen, player_screen_pos)

    # Draw mobs
    for mob in mobs:
        if mob.alive:
            mob_screen_pos = camera.apply(mob)
            mob.draw_at(screen, mob_screen_pos)

    # Draw NPCs
    for npc in npcs:
        npc_screen_pos = camera.apply(npc)
        npc.draw_at(screen, npc_screen_pos)

        # Display interaction prompt if the player is near
        if abs(player.x - npc.x) < 50 and abs(player.y - npc.y) < 50:
            npc_text = font.render(f"Press F to interact", True, BLACK)
            screen.blit(npc_text, (npc_screen_pos[0], npc_screen_pos[1] - 30))

    # Draw cities
    for city in cities:
        city_screen_pos = camera.apply(city)
        city.draw_at(screen, city_screen_pos)

        # Display interaction prompt if the player is near
        if abs(player.x - city.x) < 50 and abs(player.y - city.y) < 50:
            city_text = font.render(f"Press F to enter", True, BLACK)
            screen.blit(city_text, (city_screen_pos[0] - 5, city_screen_pos[1] - 35))

    # HUD - Health and Mana
    health_text = font.render(f"Health: {player.health}/{player.max_health}", True, RED)
    mana_text = font.render(f"Mana: {player.mana}/{player.max_mana}", True, BLUE)
    screen.blit(health_text, (10, 10))
    screen.blit(mana_text, (10, 50))

    # Display active quest objectives
    if player.active_quest:
        if not player.active_quest.completed:
            objective_text = font.render(
                f"Objective: {player.active_quest.objectives[player.active_quest.current_objective]}",
                True, BLACK
            )
            screen.blit(objective_text, (10, 90))
        else:
            completed_text = font.render("Quest Complete!", True, GREEN)
            screen.blit(completed_text, (10, 90))


# Minimap Drawing Logic
def draw_dynamic_minimap(screen, player, mobs, npcs, cities, world, SCREEN_WIDTH, SCREEN_HEIGHT):
    """
    Draw a dynamic minimap showing the player's surroundings.
    The minimap is centered on the player's position and only displays a portion of the world.
    """
    # Define the minimap size and scaling ratio
    MINIMAP_SIZE = 150
    SCALE_RATIO = world.world_width / MINIMAP_SIZE

    # Create the minimap surface
    minimap = pygame.Surface((MINIMAP_SIZE, MINIMAP_SIZE))
    minimap.fill(BLACK)

    # Calculate the player's position on the minimap
    center_x = int(player.x / SCALE_RATIO)
    center_y = int(player.y / SCALE_RATIO)

    # Draw the player
    pygame.draw.circle(minimap, GREEN, (MINIMAP_SIZE // 2, MINIMAP_SIZE // 2), 5)

    # Draw nearby cities
    for city in cities:
        city_x = int(city.x / SCALE_RATIO)
        city_y = int(city.y / SCALE_RATIO)
        if abs(center_x - city_x) < MINIMAP_SIZE // 2 and abs(center_y - city_y) < MINIMAP_SIZE // 2:
            draw_x = MINIMAP_SIZE // 2 + (city_x - center_x)
            draw_y = MINIMAP_SIZE // 2 + (city_y - center_y)
            pygame.draw.rect(minimap, BLUE, (draw_x, draw_y, 5, 5))  # City positions

    # Draw nearby mobs
    for mob in mobs:
        if mob.alive:
            mob_x = int(mob.x / SCALE_RATIO)
            mob_y = int(mob.y / SCALE_RATIO)
            if abs(center_x - mob_x) < MINIMAP_SIZE // 2 and abs(center_y - mob_y) < MINIMAP_SIZE // 2:
                draw_x = MINIMAP_SIZE // 2 + (mob_x - center_x)
                draw_y = MINIMAP_SIZE // 2 + (mob_y - center_y)
                pygame.draw.circle(minimap, RED, (draw_x, draw_y), 3)  # Mob positions

    # Draw nearby NPCs
    for npc in npcs:
        npc_x = int(npc.x / SCALE_RATIO)
        npc_y = int(npc.y / SCALE_RATIO)
        if abs(center_x - npc_x) < MINIMAP_SIZE // 2 and abs(center_y - npc_y) < MINIMAP_SIZE // 2:
            draw_x = MINIMAP_SIZE // 2 + (npc_x - center_x)
            draw_y = MINIMAP_SIZE // 2 + (npc_y - center_y)
            pygame.draw.circle(minimap, BLUE, (draw_x, draw_y), 3)  # NPC positions

    # Draw the minimap onto the screen at the top-right corner
    screen.blit(minimap, (SCREEN_WIDTH - MINIMAP_SIZE - 20, 20))

def create_static_background(world, regions, cities):
    """Pre-render static elements of the world into a surface."""
    background = pygame.Surface((world.world_width, world.world_height))
    background.fill(WHITE)  # Background color for the world
    
    # Draw regions
    for region in regions:
        region.draw_at(background, (region.x, region.y))
    
    # Draw cities
    for city in cities:
        city.draw_at(background, (city.x, city.y))
    
    return background

def is_within_view(camera: Camera, entity):
    """Check if an entity is within the camera's visible area."""
    # Get entity dimensions, default to 1x1 for points
    entity_width = getattr(entity, 'width', 30)
    entity_height = getattr(entity, 'height', 30)
    
    # Create entity rect in world coordinates
    entity_rect = pygame.Rect(entity.x, entity.y, entity_width, entity_height)
    
    # Create camera rect using camera position and screen dimensions
    camera_width = getattr(camera, 'width', SCREEN_WIDTH)
    camera_height = getattr(camera, 'height', SCREEN_HEIGHT)
    camera_rect = pygame.Rect(camera.offset_y, camera.offset_y, camera_width, camera_height)
    
    return entity_rect.colliderect(camera_rect)

def draw_minimap(screen, world, player, mobs, cities, resources):
    """
    Draw a dynamic minimap centered on the player,  showing nearby entities.
    """
    # Define minimap size and position
    minimap_width, minimap_height = 200, 200
    minimap_x, minimap_y = SCREEN_WIDTH - minimap_width - 20, 20  # Top-right corner

    # Create the minimap surface
    minimap = pygame.Surface((minimap_width, minimap_height))
    minimap.fill((0, 0, 0))  # Black background

    # Calculate scaling factors
    scale_x = minimap_width / 1000  # Display a 1000x1000 area around the player
    scale_y = minimap_height / 1000

    # Calculate the player's position on the minimap (centered)
    player_minimap_x = minimap_width // 2
    player_minimap_y = minimap_height // 2
    pygame.draw.circle(minimap, (0, 255, 0), (player_minimap_x, player_minimap_y), 5)  # Green for player

    # Draw cities relative to the player
    for city in cities:
        city_dx = (city.x - player.x) * scale_x
        city_dy = (city.y - player.y) * scale_y
        city_minimap_x = int(player_minimap_x + city_dx)
        city_minimap_y = int(player_minimap_y + city_dy)

        # Only draw cities within the minimap bounds
        if 0 <= city_minimap_x <= minimap_width and 0 <= city_minimap_y <= minimap_height:
            pygame.draw.rect(minimap, (0, 0, 255), (city_minimap_x - 2, city_minimap_y - 2, 5, 5))  # Blue for cities

    # Draw mobs relative to the player
    for mob in mobs:
        if mob.alive:
            mob_dx = (mob.x - player.x) * scale_x
            mob_dy = (mob.y - player.y) * scale_y
            mob_minimap_x = int(player_minimap_x + mob_dx)
            mob_minimap_y = int(player_minimap_y + mob_dy)

        # Only draw mobs within the minimap bounds
        if 0 <= mob_minimap_x <= minimap_width and 0 <= mob_minimap_y <= minimap_height:
            pygame.draw.circle(minimap, (255, 0, 0), (mob_minimap_x, mob_minimap_y), 3)  # Red for mobs

# Draw resources relative to the player
    for resource in resources:
        if not resource.collected:
            res_dx = (resource.x - player.x) * scale_x
            res_dy = (resource.y - player.y) * scale_y
            res_minimap_x = int(player_minimap_x + res_dx)
            res_minimap_y = int(player_minimap_y + res_dy)

            # Only draw resources within the minimap bounds
            if 0 <= res_minimap_x <= minimap_width and 0 <= res_minimap_y <= minimap_height:
                pygame.draw.circle(minimap, (255, 255, 0), (res_minimap_x, res_minimap_y), 3)  # Yellow for resources

        # Blit the minimap onto the main screen
    screen.blit(minimap, (minimap_x, minimap_y))

def generate_random_mob(world_width: int, world_height: int) -> Mob:
    """
    Generate a random mob with randomized attributes and position within the world bounds.
    """
    mob_names = ["Goblin", "Orc", "Wolf", "Bandit", "Troll"]
    loot_items = [
        Item(name="Gold Coin", description="A shiny coin.", quality="Common"),
        Item(name="Iron Ore", description="A chunk of iron.", quality="Common"),
        Weapon(name="Rusty Sword", description="A dull, rusty sword.", quality="Uncommon", damage=10),
    ]

    name = random.choice(mob_names)
    health = random.randint(30, 100)
    damage = random.randint(5, 20)
    loot = random.choice(loot_items)
    level = random.randint(1, 10)

    # Random position within world bounds
    x = random.randint(0, world_width)
    y = random.randint(0, world_height)

    return Mob(name=name, health=health, damage=damage, loot=loot, level=level, x=x, y=y)

def generate_random_city(world_width: int, world_height: int, factions: list[Faction], crafting_stations: list[CraftingStation]) -> City:
    """
    Generate a random city with randomized attributes and position.
    """
    city_names = ["Ironhold", "Silverpeak", "Oakvale", "Rivermouth", "Sunspire"]
    shop_items = [
        Item(name="Health Potion", description="Restores health.", quality="Common", price=10),
        Weapon(name="Steel Sword", description="A sharp blade.", quality="Uncommon", damage=25, price=50),
        Armor(name="Leather Armor", description="Basic protection.", quality="Common", defense=5, price=30)
    ]

    name = random.choice(city_names)
    population = random.randint(500, 5000)
    guards = random.randint(50, 500)

    # Randomly assign a faction
    faction = random.choice(factions)

    # Generate random shops
    shops = [
        Shop(
            name=f"{name} General Store",
            items=random.sample(shop_items, random.randint(1, 3)),
            faction=faction
        )
    ]

    # Add crafting stations
    city_crafting_stations = random.sample(crafting_stations, random.randint(1, len(crafting_stations)))

    # Random position within world bounds
    x = random.randint(0, world_width)
    y = random.randint(0, world_height)

    return City(name=name, population=population, guards=guards, faction=faction, shops=shops, crafting_stations=city_crafting_stations, x=x, y=y)






for _ in range(5):
    cities.append(generate_random_city(5000, 5000, [guild_of_merchants, dark_brotherhood], crafting_stations))

for _ in range(10):
    mobs.append(generate_random_mob(5000, 5000))


show_full_map = False  # Boolean to track the map view state

def draw_full_world_map(screen, world: GameWorld, player: Character, mobs: list[Mob], cities: list[City], resources: list[Resource]):
    """
    Draw the full world map, showing all regions, cities, mobs, and resources.
    """
    # Define full map size and position
    map_width, map_height = 400, 400  # Full map dimensions
    map_x, map_y = (SCREEN_WIDTH - map_width) // 2, (SCREEN_HEIGHT - map_height) // 2  # Center on screen

    # Create the full map surface
    world_map = pygame.Surface((map_width, map_height))
    world_map.fill((0, 0, 0))  # Black background

    # Calculate scaling factors
    scale_x = map_width / world.width
    scale_y = map_height / world.height

    # Draw cities
    for city in cities:
        city_map_x = int(city.x * scale_x)
        city_map_y = int(city.y * scale_y)
        pygame.draw.rect(world_map, (0, 0, 255), (city_map_x - 2, city_map_y - 2, 5, 5))  # Blue for cities

    # Draw mobs
    for mob in mobs:
        if mob.alive:
            mob_map_x = int(mob.x * scale_x)
            mob_map_y = int(mob.y * scale_y)
            pygame.draw.circle(world_map, (255, 0, 0), (mob_map_x, mob_map_y), 3)  # Red for mobs

    # Draw resources
    for resource in resources:
        if not resource.collected:
            resource_map_x = int(resource.x * scale_x)
            resource_map_y = int(resource.y * scale_y)
            pygame.draw.circle(world_map, (255, 255, 0), (resource_map_x, resource_map_y), 2)  # Yellow for resources
    for npc in npcs:
        npc_map_x = int(npc.x * scale_x)
        npc_map_y = int(npc.y * scale_y)
        pygame.draw.rect(world_map, (0, 0, 255), (npc_map_x, npc_map_y, 3, 3))  # Blue for npcs

    # Draw the player's position
    player_map_x = int(player.x * scale_x)
    player_map_y = int(player.y * scale_y)
    pygame.draw.rect(world_map, (0, 255, 0), (player_map_x, player_map_y, 5, 5))  # Green for player

    # Blit the full map onto the main screen
    screen.blit(world_map, (map_x, map_y))

    # Optional: Add a border and title for the map
    pygame.draw.rect
