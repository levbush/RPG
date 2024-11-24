from random import randint
from dataclasses import dataclass
import pygame
from pygame.locals import *
import threading
import time
import random
from collections import defaultdict


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
    def __init__(self, name, giver, storyline, objectives, rewards: list, reputation: float = 0, gold: int = 10, experience: int = 50):
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
            self.rewarded = True
        else:
            print(f"Quest '{self.name}' is not completed. Rewards unavailable.")

class Shop:
    def __init__(self, name: str, items: list[Item]):
        """
        Initialize the shop with a name and a list of items for sale.
        """
        self.name = name
        self.items = items

    def display_items(self):
        """Display items available in the shop."""
        print(f"Welcome to {self.name}! Here are the items available:")
        for idx, item in enumerate(self.items, start=1):
            price = getattr(item, 'price', 0)
            print(f"{idx}. {item.name} - {price} gold")

    def buy(self, player: 'Character', item_index: int):
        """
        Allow the player to buy an item from the shop.
        :param player: The player buying the item.
        :param item_index: The index of the item to buy.
        """
        if item_index < 1 or item_index > len(self.items):
            print("Invalid selection.")
            return

        item = self.items[item_index - 1]
        price = getattr(item, 'price', 0)

        if player.gold >= price:
            player.gold -= price
            player.inventory.add_item(item)
            print(f"You bought {item.name} for {price} gold.")
        else:
            print("You don't have enough gold to buy this item.")

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
    def __init__(self, name, station_type, x, y):
        """
        Initialize the crafting station.
        :param name: Name of the station (e.g., "Blacksmith Forge").
        """
        self.name = name
        self.station_type = station_type
        self.x = x
        self.y = y

    def draw(self, screen):
        """Draw the crafting station on the screen."""
        pygame.draw.rect(screen, self.color, (self.x, self.y, 40, 40))

    def interact(self, player: 'Character', screen):
        """Handle interaction with the crafting station."""
        menu_font = pygame.font.Font(None, 36)
        title_font = pygame.font.Font(None, 48)
        running_crafting = True
        selected_recipe = 0

        while running_crafting:
            # Fill the screen for the crafting menu
            screen.fill(WHITE)

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
                        recipe = player.inventory.known_recipes[selected_recipe]
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
        options = ["Visit Shop", "Rest at Inn", "Use Crafting Station", "Talk to Locals", "Leave"]

        while running_city:
            # Fill screen with city background
            screen.fill(WHITE)

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
                        elif selected_option == 1:  # Rest at inn
                            print(f"{player.name} rested and recovered health.")
                            player.rest(10)
                        elif selected_option == 2:  # Use crafting station
                            self.visit_crafting_station(player, screen)
                        elif selected_option == 3:  # Talk to locals
                            print("You chat with the locals and learn about the city.")
                        elif selected_option == 4:  # Leave the city
                            running_city = False

    def draw(self, screen):
        """Draw the city on the screen."""
        pygame.draw.circle(screen, self.color, (self.x, self.y), 10)  # City marker
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
            if material not in [i[0] for i in self.contents] or self.contents[[i[0] for i in self.contents].index(item)][1] < count:
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
        if self.capacity >= len(self.contents) + 1 or item.name in self.contents:
            if item.name in self.contents:
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


    # def remove_item(self, item: Item):
    #     """Remove an item from the inventory."""
    #     if item in [i[0] for i in self.contents]:
    #         self.contents.remove(item)
    #         return item
    #     else:
    #         print('Item not in inventory')
    #         print()
    #         return None
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
    def __init__(self, name: str, inventory: Inventory, character_class: str, max_health: float=100.0, strength: float=10.0, intelligence: float=10.0, agility: float=10.0, luck: float=10.0,  experience: float=0.0, level: int=1, saturation: float=10.0, max_mana: float=15.0, quests:list[Quest]=[], reputation: dict['Faction': int]={}, completed_quests: list[Quest]=[], city: City=None, race: str='Human', special_abilities: list[str]=[], achievements: list[str]=[], skills: list['Skill']=[], crafting_level: int = 1, crafting_experience: float = 0, gold: int = 100, x: float=400, y: float=300):
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
    
    def draw(self, screen):
        """Draw the character on the screen."""
        if self.alive:
            pygame.draw.rect(screen, self.color, (self.x, self.y, 30, 30))
            font = pygame.font.Font(None, 24)
            text = font.render(self.name, True, (0, 0, 0))
            screen.blit(text, (self.x, self.y - 15))

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
                    self.disequip_weapon(self.right_hand)
                self.right_hand = weapon
                self.damage += weapon.damage
                print(f"{weapon.name} equipped in right hand. Your damage: {self.damage}")
            elif hand == 'left':
                if self.left_hand:
                    self.disequip_weapon(self.left_hand)
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

    def disequip_weapon(self, weapon: Weapon):
        """Disequip a weapon."""
        if weapon in [i[0] for i in self.inventory.contents]:
            if self.right_hand == weapon:
                self.right_hand = None
                self.damage -= weapon.damage
            elif self.left_hand == weapon:
                self.left_hand = None
                self.damage = weapon.damage
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
                    self.disequip_armor(self.armor_chest)
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
                    self.disequip_armor(self.armor_head)
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
                    self.disequip_armor(self.armor_legs)
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
                    self.disequip_armor(self.armor_feet)
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

    def disequip_armor(self, armor: Armor):
        """Disequip an armor."""
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
                    print(f'{armor.name} disequipped')
                    print()
                elif self.armor_head == armor:
                    self.armor_head = None
                    self.defense -= armor.defense
                    if self.health == self.max_health:
                        self.health -= armor.health
                    self.max_health -= armor.health
                    self.strength -= armor.strength
                    self.agility -= armor.agility
                    print(f'{armor.name} disequipped')
                    print()
                elif self.armor_legs == armor:
                    self.armor_legs = None
                    self.defense -= armor.defense
                    if self.health == self.max_health:
                        self.health -= armor.health
                    self.max_health -= armor.health
                    self.strength -= armor.strength
                    self.agility -= armor.agility
                    print(f'{armor.name} disequipped')
                    print()
                elif self.armor_feet == armor:
                    self.armor_feet = None
                    self.defense -= armor.defense
                    if self.health == self.max_health:
                        self.health -= armor.health
                    self.max_health -= armor.health
                    self.strength -= armor.strength
                    self.agility -= armor.agility
                    print(f'{armor.name} disequipped')
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
                self.disequip_weapon(self.right_hand)
        if self.left_hand:
            self.left_hand.durskill -= 1
            if self.left_hand.durskill <= 0:
                print(f"{self.left_hand.name} has broken!")
                print()
                self.inventory.remove_item(self.left_hand)
                self.disequip_weapon(self.left_hand)

        self.saturation -= 0.5
    def consume(self, item: Item):
        """Consume an item."""
        if not self.check_requirements(item):
            return
        if item in [i[0] for i in self.inventory.contents]:
            try:
                if item.item_type == 'Potion': # potion is a separate class but depends on Item
                    if item.potion_type == 'Health':
                        self.health += item.value
                    elif item.potion_type == 'Strength':
                        self.strength += item.value
                    elif item.potion_type == 'Agility':
                        self.agility += item.value
                    elif item.potion_type == 'Defense':
                        self.defense += item.value
                    elif item.potion_type == 'Mana':
                        self.mana += item.value
                    if self.health > self.max_health:
                        self.health = self.max_health
                    if self.mana > self.max_mana:
                        self.mana = self.max_mana
                    print(f'{self.name} consumed {item.name} ({item.potion_type}). Health: {self.health}, Mana: {self.mana}')
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
                print('Consume: Invalid item')
                print()
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

    def respawn_after_delay(self):
        """Respawn after a delay"""
        sleep(self.respawn_time)  # Delay for respawn
        self.respawn()
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

    def interact(self, player: 'Character'):
        """Give a quest to the player."""
        for quest in self.quests:
            if quest in player.quests and quest.completed:
                player.complete_quest(quest)
            elif quest not in player.quests and quest not in player.completed_quests:
                player.accept_quest(quest)
                print(f"{self.name} has given the quest: '{quest.name}'.")
                return
        print(f"{self.name} has no quests available for {player.name}.")
    def draw(self, screen):
        pygame.draw.rect(screen, BLUE, (self.x, self.y, 30, 30))
        font = pygame.font.Font(None, 24)
        text = font.render(self.name, True, (0, 0, 0))
        screen.blit(text, (self.x, self.y - 15))

class Faction: # Do not used yet. Planning to add factions and influence with some unique buffs or debuffs.
    def __init__(self, name: str, description: str='', leader: Character=None, members: list[Character]=[]):
        self.name = name
        self.description = description
        self.leader = leader
        self.members = members
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


class World: # World with cities, mobs, npcs, and events.
    def __init__(self, name: str, cities: list[City], npcs: list[NPC], mobs: list[Mob]):
        self.name = name
        self.cities = cities
        self.npcs = npcs
        self.mobs = mobs
        self.events = []  # Track world events

    def log_event(self, event_type: str, details: dict):
        """Log world events dynamically."""
        self.events.append({"type": event_type, "details": details})
        print(f"World Event Logged: {event_type} - {details}")

def render_shop_menu(screen, shop, player):
    """Render the shop menu and handle player interaction."""
    menu_font = pygame.font.Font(None, 36)
    title_font = pygame.font.Font(None, 48)
    running_shop = True
    selected_item = 0  # Index of the currently selected item

    while running_shop:
        # Fill the screen for the shop menu
        screen.fill(WHITE)

        # Render shop title
        title_text = title_font.render(f"Welcome to {shop.name}", True, BLACK)
        screen.blit(title_text, (50, 50))

        # Render shop items
        y_offset = 150
        for i, item in enumerate(shop.items):
            color = BLACK if i != selected_item else RED  # Highlight selected item
            item_text = menu_font.render(
                f"{item.name} - {item.quality} - {item.price} Gold", True, color
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
                    if player.gold >= item.price:
                        player.gold -= item.price
                        player.inventory.add_item(item)
                        print(f"You bought {item.name}!")
                    else:
                        print("Not enough gold!")
                elif event.key == K_ESCAPE:  # Exit the shop menu
                    running_shop = False

def render_inventory_menu(screen, player: Character):
    """Render the inventory menu and handle player interaction."""
    menu_font = pygame.font.Font(None, 36)
    title_font = pygame.font.Font(None, 48)
    running_inventory = True
    selected_item = 0  # Index of the currently selected item

    while running_inventory:
        # Fill the screen for the inventory menu
        screen.fill(WHITE)

        # Render inventory title
        title_text = title_font.render("Inventory", True, BLACK)
        screen.blit(title_text, (50, 50))

        # Render inventory items
        y_offset = 150
        for i, item in enumerate(player.inventory.contents):
            color = BLACK if i != selected_item else RED  # Highlight selected item
            item_text = menu_font.render(
                f"{item[0].name} - {item[0].quality} - {item[0].description}", True, color
            )
            screen.blit(item_text, (50, y_offset))
            y_offset += 40

        # Render player's gold
        gold_text = menu_font.render(f"Gold: {player.gold}", True, BLACK)
        screen.blit(gold_text, (50, y_offset + 20))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()
            elif event.type == KEYDOWN:
                if event.key == K_DOWN:
                    selected_item = (selected_item + 1) % len(player.inventory.contents)
                elif event.key == K_UP:
                    selected_item = (selected_item - 1) % len(player.inventory.contents)
                elif event.key == K_RIGHT:  # Use selected item
                    item = player.inventory.contents[selected_item][0]
                    if issubclass(item.__class__, Weapon):
                        print(f"Equipping {item.name}...")
                        player.equip_weapon(item)
                    elif issubclass(item.__class__, Armor):
                        player.equip_armor(item)
                    elif issubclass(item.__class__, Artifact):
                        pass
                    elif issubclass(item.__class__, Item):
                        player.consume(item)
                    else:
                        print("Unusable item!")
                elif event.key == K_q:  # Drop selected item
                    item = player.inventory.contents[selected_item][0]
                    try:
                        del player.inventory.contents[selected_item]
                        print(f"Dropped {item.name}.")
                    except IndexError:
                        print("No item selected!")
                    break
                elif event.key == K_ESCAPE:  # Exit the inventory menu
                    running_inventory = False