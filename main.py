



import pygame
import json
import sys
import numpy as np
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import math
import random
import os
import pygame.gfxdraw  # Aggiungi questo import nel file principale
from typing import List, Tuple


from dataclasses import dataclass
from enum import Enum







def resource_path(relative_path):
    """Ottiene il path corretto sia per sviluppo che per exe"""
    if hasattr(sys, '_MEIPASS'):
        # Running in PyInstaller bundle
        return os.path.join(sys._MEIPASS, relative_path)
    # Running in normal Python
    return os.path.join(os.path.abspath("."), relative_path)




# ============== SOUND SYNTHESIZER ==============
class SoundSynthesizer:
    def __init__(self, sample_rate: int = 22050):
        pygame.mixer.init(frequency=sample_rate, size=-16, channels=2, buffer=512)
        self.sample_rate = sample_rate
        self.sounds_cache = {}
    
    def _generate_wave(self, frequency: float, duration: float, wave_type: str = 'sine') -> np.ndarray:
        num_samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, num_samples, False)
        
        if wave_type == 'sine':
            wave = np.sin(2 * np.pi * frequency * t)
        elif wave_type == 'square':
            wave = np.sign(np.sin(2 * np.pi * frequency * t))
        elif wave_type == 'sawtooth':
            wave = 2 * (t * frequency - np.floor(0.5 + t * frequency))
        elif wave_type == 'triangle':
            wave = 2 * np.abs(2 * (t * frequency - np.floor(0.5 + t * frequency))) - 1
        else:
            wave = np.sin(2 * np.pi * frequency * t)
        return wave
    
    def _apply_envelope(self, wave: np.ndarray, attack: float, decay: float, sustain: float, release: float) -> np.ndarray:
        total_samples = len(wave)
        envelope = np.ones(total_samples)
        
        attack_samples = int(attack * self.sample_rate)
        decay_samples = int(decay * self.sample_rate)
        release_samples = int(release * self.sample_rate)
        
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        if decay_samples > 0:
            decay_end = attack_samples + decay_samples
            envelope[attack_samples:decay_end] = np.linspace(1, sustain, decay_samples)
        
        sustain_start = attack_samples + decay_samples
        sustain_end = total_samples - release_samples
        if sustain_end > sustain_start:
            envelope[sustain_start:sustain_end] = sustain
        if release_samples > 0:
            envelope[-release_samples:] = np.linspace(sustain, 0, release_samples)
        return wave * envelope
    
    def _to_pygame_sound(self, wave: np.ndarray, volume: float = 0.3) -> pygame.mixer.Sound:
        wave = wave * volume
        wave = np.clip(wave, -1.0, 1.0)
        stereo_wave = np.column_stack((wave, wave))
        sound_array = (stereo_wave * 32767).astype(np.int16)
        return pygame.mixer.Sound(sound_array)
    
    def create_blip(self, pitch: int = 0) -> pygame.mixer.Sound:
        cache_key = f"blip_{pitch}"
        if cache_key in self.sounds_cache:
            return self.sounds_cache[cache_key]
        freq = 440 + (pitch * 100)
        wave = self._generate_wave(freq, 0.05, 'square')
        wave = self._apply_envelope(wave, 0.01, 0.01, 0.5, 0.03)
        sound = self._to_pygame_sound(wave, 0.2)
        self.sounds_cache[cache_key] = sound
        return sound
    
    def create_select(self) -> pygame.mixer.Sound:
        if "select" in self.sounds_cache:
            return self.sounds_cache["select"]
        wave1 = self._generate_wave(440, 0.08, 'square')
        wave2 = self._generate_wave(660, 0.08, 'square')
        wave = np.concatenate([wave1, wave2])
        wave = self._apply_envelope(wave, 0.01, 0.02, 0.7, 0.05)
        sound = self._to_pygame_sound(wave, 0.25)
        self.sounds_cache["select"] = sound
        return sound
    
    def create_back(self) -> pygame.mixer.Sound:
        if "back" in self.sounds_cache:
            return self.sounds_cache["back"]
        wave = self._generate_wave(330, 0.1, 'sine')
        wave = self._apply_envelope(wave, 0.01, 0.03, 0.5, 0.06)
        sound = self._to_pygame_sound(wave, 0.2)
        self.sounds_cache["back"] = sound
        return sound
    
    def create_game_start(self) -> pygame.mixer.Sound:
        if "game_start" in self.sounds_cache:
            return self.sounds_cache["game_start"]
        freqs = [262, 330, 392, 523]
        waves = [self._generate_wave(freq, 0.12, 'sine') for freq in freqs]
        wave = np.concatenate(waves)
        wave = self._apply_envelope(wave, 0.01, 0.02, 0.8, 0.1)
        sound = self._to_pygame_sound(wave, 0.3)
        self.sounds_cache["game_start"] = sound
        return sound
    
    def create_score_point(self) -> pygame.mixer.Sound:
        if "score_point" in self.sounds_cache:
            return self.sounds_cache["score_point"]
        wave = self._generate_wave(880, 0.06, 'triangle')
        wave = self._apply_envelope(wave, 0.005, 0.01, 0.6, 0.045)
        sound = self._to_pygame_sound(wave, 0.25)
        self.sounds_cache["score_point"] = sound
        return sound
    
    def create_game_over(self) -> pygame.mixer.Sound:
        if "game_over" in self.sounds_cache:
            return self.sounds_cache["game_over"]
        freqs = [440, 370, 311, 233]
        waves = [self._generate_wave(freq, 0.2, 'sawtooth') for freq in freqs]
        wave = np.concatenate(waves)
        wave = self._apply_envelope(wave, 0.02, 0.05, 0.7, 0.2)
        sound = self._to_pygame_sound(wave, 0.3)
        self.sounds_cache["game_over"] = sound
        return sound
    
    def create_high_score(self) -> pygame.mixer.Sound:
        if "high_score" in self.sounds_cache:
            return self.sounds_cache["high_score"]
        freqs = [523, 659, 784, 1047]
        waves = []
        for i, freq in enumerate(freqs):
            duration = 0.15 if i < 3 else 0.3
            waves.append(self._generate_wave(freq, duration, 'sine'))
        wave = np.concatenate(waves)
        wave = self._apply_envelope(wave, 0.01, 0.03, 0.8, 0.2)
        sound = self._to_pygame_sound(wave, 0.35)
        self.sounds_cache["high_score"] = sound
        return sound
    
    def create_hit(self) -> pygame.mixer.Sound:
        if "hit" in self.sounds_cache:
            return self.sounds_cache["hit"]
        wave = self._generate_wave(200, 0.08, 'square')
        noise = np.random.uniform(-0.5, 0.5, len(wave))
        wave = wave * 0.3 + noise * 0.7
        wave = self._apply_envelope(wave, 0.001, 0.02, 0.3, 0.057)
        sound = self._to_pygame_sound(wave, 0.2)
        self.sounds_cache["hit"] = sound
        return sound
    
    def create_powerup(self) -> pygame.mixer.Sound:
        """Power-up collected sound - ascending magical chime"""
        if "powerup" in self.sounds_cache:
            return self.sounds_cache["powerup"]
        freqs = [523, 659, 784, 1047, 1319]  # C5, E5, G5, C6, E6
        waves = []
        for freq in freqs:
            wave = self._generate_wave(freq, 0.08, 'sine')
            # Add harmonic for sparkle effect
            harmonic = self._generate_wave(freq * 2, 0.08, 'sine') * 0.3
            waves.append(wave + harmonic)
        wave = np.concatenate(waves)
        wave = self._apply_envelope(wave, 0.005, 0.02, 0.8, 0.1)
        sound = self._to_pygame_sound(wave, 0.28)
        self.sounds_cache["powerup"] = sound
        return sound
    
    def create_brick_break(self) -> pygame.mixer.Sound:
        """Brick breaking sound - satisfying crunch"""
        if "brick_break" in self.sounds_cache:
            return self.sounds_cache["brick_break"]
        # Combination of tone and noise for impact
        wave = self._generate_wave(150, 0.1, 'square')
        noise = np.random.uniform(-0.6, 0.6, len(wave))
        wave = wave * 0.4 + noise * 0.6
        wave = self._apply_envelope(wave, 0.001, 0.03, 0.3, 0.066)
        sound = self._to_pygame_sound(wave, 0.22)
        self.sounds_cache["brick_break"] = sound
        return sound
    
    def create_laser_shoot(self) -> pygame.mixer.Sound:
        """Laser shooting sound - sci-fi pew"""
        if "laser_shoot" in self.sounds_cache:
            return self.sounds_cache["laser_shoot"]
        # Descending frequency for laser effect
        duration = 0.12
        num_samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, num_samples, False)
        # Frequency sweep from 1200 to 400 Hz
        freq_sweep = 1200 - (800 * t / duration)
        wave = np.sin(2 * np.pi * freq_sweep * t)
        wave = self._apply_envelope(wave, 0.001, 0.02, 0.5, 0.099)
        sound = self._to_pygame_sound(wave, 0.2)
        self.sounds_cache["laser_shoot"] = sound
        return sound
    
    def create_level_complete(self) -> pygame.mixer.Sound:
        """Level complete fanfare - victory jingle"""
        if "level_complete" in self.sounds_cache:
            return self.sounds_cache["level_complete"]
        # Victory melody: C-E-G-C (arpeggiated chord)
        freqs = [523, 659, 784, 1047]
        waves = []
        for i, freq in enumerate(freqs):
            duration = 0.15 if i < 3 else 0.35
            wave = self._generate_wave(freq, duration, 'triangle')
            # Add fifth harmonic for richness
            harmonic = self._generate_wave(freq * 1.5, duration, 'sine') * 0.2
            waves.append(wave + harmonic)
        wave = np.concatenate(waves)
        wave = self._apply_envelope(wave, 0.01, 0.03, 0.85, 0.15)
        sound = self._to_pygame_sound(wave, 0.32)
        self.sounds_cache["level_complete"] = sound
        return sound
    
    def create_ball_lost(self) -> pygame.mixer.Sound:
        """Ball lost sound - descending sad tone"""
        if "ball_lost" in self.sounds_cache:
            return self.sounds_cache["ball_lost"]
        freqs = [440, 370, 311]  # Descending notes
        waves = [self._generate_wave(freq, 0.15, 'sine') for freq in freqs]
        wave = np.concatenate(waves)
        wave = self._apply_envelope(wave, 0.01, 0.05, 0.6, 0.15)
        sound = self._to_pygame_sound(wave, 0.25)
        self.sounds_cache["ball_lost"] = sound
        return sound
    
    def create_combo(self) -> pygame.mixer.Sound:
        """Combo hit sound - quick ascending beep"""
        if "combo" in self.sounds_cache:
            return self.sounds_cache["combo"]
        wave = self._generate_wave(660, 0.05, 'square')
        wave2 = self._generate_wave(880, 0.05, 'square')
        wave = np.concatenate([wave, wave2])
        wave = self._apply_envelope(wave, 0.005, 0.01, 0.7, 0.035)
        sound = self._to_pygame_sound(wave, 0.2)
        self.sounds_cache["combo"] = sound
        return sound
    
    def create_paddle_hit(self) -> pygame.mixer.Sound:
        """Paddle hit sound - bounce effect"""
        if "paddle_hit" in self.sounds_cache:
            return self.sounds_cache["paddle_hit"]
        wave = self._generate_wave(330, 0.08, 'triangle')
        noise = np.random.uniform(-0.3, 0.3, len(wave))
        wave = wave * 0.7 + noise * 0.3
        wave = self._apply_envelope(wave, 0.001, 0.015, 0.4, 0.064)
        sound = self._to_pygame_sound(wave, 0.22)
        self.sounds_cache["paddle_hit"] = sound
        return sound
    
    def create_wall_bounce(self) -> pygame.mixer.Sound:
        """Wall bounce sound - sharp tick"""
        if "wall_bounce" in self.sounds_cache:
            return self.sounds_cache["wall_bounce"]
        wave = self._generate_wave(250, 0.06, 'square')
        noise = np.random.uniform(-0.4, 0.4, len(wave))
        wave = wave * 0.5 + noise * 0.5
        wave = self._apply_envelope(wave, 0.001, 0.01, 0.3, 0.049)
        sound = self._to_pygame_sound(wave, 0.18)
        self.sounds_cache["wall_bounce"] = sound
        return sound
    
    def create_multiball(self) -> pygame.mixer.Sound:
        """Multiball activation - explosive sound"""
        if "multiball" in self.sounds_cache:
            return self.sounds_cache["multiball"]
        # Multiple frequencies at once for chaotic effect
        wave1 = self._generate_wave(440, 0.2, 'square')
        wave2 = self._generate_wave(554, 0.2, 'square')
        wave3 = self._generate_wave(659, 0.2, 'square')
        wave = (wave1 + wave2 + wave3) / 3
        wave = self._apply_envelope(wave, 0.01, 0.04, 0.7, 0.15)
        sound = self._to_pygame_sound(wave, 0.3)
        self.sounds_cache["multiball"] = sound
        return sound
    
    def create_shield_activate(self) -> pygame.mixer.Sound:
        """Shield/protection activation - rising protective sound"""
        if "shield_activate" in self.sounds_cache:
            return self.sounds_cache["shield_activate"]
        # Rising frequency sweep
        duration = 0.25
        num_samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, num_samples, False)
        freq_sweep = 200 + (600 * t / duration)
        wave = np.sin(2 * np.pi * freq_sweep * t)
        wave = self._apply_envelope(wave, 0.01, 0.05, 0.8, 0.19)
        sound = self._to_pygame_sound(wave, 0.25)
        self.sounds_cache["shield_activate"] = sound
        return sound








# ============== ANIMATED BACKGROUND ==============
class AnimatedBackground:
    def __init__(self):
        self.particles = []
        self.stars = []
        self.time = 0.0
        
        for _ in range(60):
            self.stars.append({
                'x': random.randint(0, 1280),
                'y': random.randint(0, 720),
                'speed': random.uniform(0.3, 1.5),
                'size': random.randint(1, 3),
                'brightness': random.uniform(0.4, 1.0)
            })
        
        self.speed_lines = []
        for _ in range(20):
            self.speed_lines.append({
                'x': random.randint(-100, 1380),
                'y': random.randint(0, 720),
                'speed': random.uniform(5, 15),
                'length': random.randint(40, 120),
                'thickness': random.randint(1, 3)
            })
    
    def update(self, dt: float):
        self.time += dt
        for star in self.stars:
            star['x'] -= star['speed'] * dt * 10
            if star['x'] < 0:
                star['x'] = 1280
                star['y'] = random.randint(0, 720)
        for line in self.speed_lines:
            line['x'] -= line['speed'] * dt * 100
            if line['x'] + line['length'] < 0:
                line['x'] = 1280 + random.randint(0, 100)
                line['y'] = random.randint(0, 720)
    
    def draw(self, surface: pygame.Surface):
        for y in range(720):
            factor = y / 720
            r = int(5 + math.sin(self.time * 0.5 + factor) * 3)
            g = int(8 + math.sin(self.time * 0.3 + factor * 1.5) * 3)
            b = int(25 + math.sin(self.time * 0.4 + factor * 2) * 5)
            pygame.draw.line(surface, (r, g, b), (0, y), (1280, y))
        
        for star in self.stars:
            brightness = int(star['brightness'] * 255)
            twinkle = abs(math.sin(self.time * 2 + star['x'] * 0.01)) * 0.3 + 0.7
            color_val = int(brightness * twinkle)
            color = (color_val, color_val, min(255, color_val + 50))
            if star['size'] > 1:
                pygame.draw.circle(surface, color, (int(star['x']), int(star['y'])), star['size'])
            else:
                try:
                    surface.set_at((int(star['x']), int(star['y'])), color)
                except:
                    pass
        
        for line in self.speed_lines:
            color = (100, 120, 200)
            pygame.draw.line(surface, color, (int(line['x']), int(line['y'])), 
                           (int(line['x'] + line['length']), int(line['y'])), line['thickness'])

# ============== CAROUSEL ITEM ==============
class CarouselItem:
    def __init__(self, name: str, description: str, image_surface: pygame.Surface):
        self.name = name
        self.description = description
        self.image = image_surface
        self.font_title = pygame.font.Font(None, 75)
        self.font_desc = pygame.font.Font(None, 38)
    
    def draw(self, surface: pygame.Surface, x: int, y: int, alpha: float = 1.0, offset_x: float = 0):
        draw_x = int(x + offset_x)
        temp_surface = pygame.Surface((900, 550), pygame.SRCALPHA)
        temp_surface.fill((0, 0, 0, 0))
        
        img_y = 40
        img_rect = self.image.get_rect(center=(450, img_y + 175))
        temp_surface.blit(self.image, img_rect)
        
        text_y = 390
        for offset in [(0, 4), (4, 0), (0, -4), (-4, 0), (3, 3), (-3, 3), (3, -3), (-3, -3)]:
            outline = self.font_title.render(self.name, True, (0, 0, 0))
            temp_surface.blit(outline, outline.get_rect(center=(450 + offset[0], text_y + offset[1])))
        
        title = self.font_title.render(self.name, True, (255, 230, 0))
        temp_surface.blit(title, title.get_rect(center=(450, text_y)))
        
        desc = self.font_desc.render(self.description, True, (230, 240, 255))
        temp_surface.blit(desc, desc.get_rect(center=(450, text_y + 60)))
        
        if alpha < 1.0:
            temp_surface.set_alpha(int(alpha * 255))
        surface.blit(temp_surface, (draw_x, y))

# ============== MENU CAROUSEL ==============
class MenuCarousel:
    def __init__(self, images_dir: str = "menu_images"):
        self.images_dir = Path(resource_path(images_dir))
        self.images_dir.mkdir(exist_ok=True)
        self.items: List[CarouselItem] = []
        self.current_index = 0
        self.is_transitioning = False
        self.transition_progress = 0.0
        self.transition_duration = 0.35
        self.transition_direction = 0
        self.target_index = 0
    
    def add_item(self, name: str, description: str):
        image = self._load_or_create_image(name)
        self.items.append(CarouselItem(name, description, image))
    
    def _load_or_create_image(self, item_name: str) -> pygame.Surface:
        safe_name = "".join(c for c in item_name if c.isalnum() or c in (' ', '_')).strip()
        image_path = self.images_dir / f"{safe_name.replace(' ', '_')}.png"
        target_width, target_height = 600, 300
        
        if image_path.exists():
            try:
                img = pygame.image.load(str(image_path)).convert_alpha()
                scale = min(target_width / img.get_width(), target_height / img.get_height())
                new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
                return pygame.transform.smoothscale(img, new_size)
            except:
                pass
        return self._create_placeholder(item_name, target_width, target_height)
    
    def _create_placeholder(self, item_name: str, width: int, height: int) -> pygame.Surface:
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        center_x, center_y = width // 2, height // 2
        
        num_rays = 12
        for i in range(num_rays):
            angle = (i / num_rays) * 2 * math.pi
            inner_radius, outer_radius = 60, 100
            x1 = center_x + math.cos(angle) * inner_radius
            y1 = center_y + math.sin(angle) * inner_radius
            x2 = center_x + math.cos(angle) * outer_radius
            y2 = center_y + math.sin(angle) * outer_radius
            points = [(center_x, center_y), (int(x1), int(y1)), (int(x2), int(y2))]
            color = (255, 200, 0, 100) if i % 2 == 0 else (255, 150, 0, 80)
            pygame.draw.polygon(surface, color, points)
        
        font_huge = pygame.font.Font(None, 150)
        question = font_huge.render("?", True, (255, 255, 255))
        surface.blit(question, question.get_rect(center=(center_x, center_y)))
        return surface
    
    def navigate(self, direction: int):
        if self.is_transitioning or not self.items:
            return
        self.target_index = (self.current_index + direction) % len(self.items)
        self.transition_direction = direction
        self.is_transitioning = True
        self.transition_progress = 0.0
    
    def update(self, dt: float):
        if not self.is_transitioning:
            return
        self.transition_progress += dt / self.transition_duration
        if self.transition_progress >= 1.0:
            self.transition_progress = 1.0
            self.current_index = self.target_index
            self.is_transitioning = False
    
    def draw(self, surface: pygame.Surface, x: int, y: int):
        if not self.items:
            return
        if not self.is_transitioning:
            self.items[self.current_index].draw(surface, x, y, 1.0, 0)
        else:
            progress = 1 - pow(1 - self.transition_progress, 3)
            slide_distance = 1000
            offset = progress * slide_distance * self.transition_direction
            self.items[self.current_index].draw(surface, x, y, 1.0 - progress * 0.6, offset)
            self.items[self.target_index].draw(surface, x, y, progress, 
                                              -slide_distance * self.transition_direction + offset)
    
    def get_current_index(self) -> int:
        return self.current_index
    
    def get_item_count(self) -> int:
        return len(self.items)



# ============== CONFIG ==============
class Config:
    CONFIG_FILE = "arcade_config.json"
    VALID_RESOLUTIONS = [(1280, 720), (1920, 1080)]
    
    def __init__(self):
        self.spinner_sensitivity = 50
        self.resolution = (1280, 720)
        self.fullscreen = False
        self.load()
    
    def load(self):
        try:
            with open(self.CONFIG_FILE, 'r') as f:
                data = json.load(f)
                self.spinner_sensitivity = max(10, min(200, data.get('spinner_sensitivity', 50)))
                res = tuple(data.get('resolution', [1280, 720]))
                self.resolution = res if res in self.VALID_RESOLUTIONS else (1280, 720)
                self.fullscreen = bool(data.get('fullscreen', False))
        except (FileNotFoundError, json.JSONDecodeError):
            self.save()
    
    def save(self):
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump({
                'spinner_sensitivity': self.spinner_sensitivity,
                'resolution': list(self.resolution),
                'fullscreen': self.fullscreen
            }, f, indent=2)




# ============== HIGH SCORE MANAGER ==============
class HighScoreManager:
    def __init__(self, scores_dir: str = "scores"):
        self.scores_dir = Path(scores_dir)
        self.scores_dir.mkdir(exist_ok=True)
        self.cache = {}
    
    def _get_scores_file(self, game_name: str) -> Path:
        safe_name = "".join(c for c in game_name if c.isalnum() or c in (' ', '_')).rstrip()
        return self.scores_dir / f"{safe_name.replace(' ', '_')}_scores.json"
    
    def load_scores(self, game_name: str) -> List[Dict]:
        if game_name in self.cache:
            return self.cache[game_name]
        scores_file = self._get_scores_file(game_name)
        try:
            with open(scores_file, 'r') as f:
                scores = json.load(f).get('scores', [])[:10]
                self.cache[game_name] = scores
                return scores
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def is_high_score(self, game_name: str, score: int) -> bool:
        scores = self.load_scores(game_name)
        return len(scores) < 10 or score > scores[-1]['score']
    
    def save_score(self, game_name: str, score: int, player_name: str = "AAA") -> int:
        scores = self.load_scores(game_name)
        new_entry = {
            'score': score,
            'player': player_name.upper(),
            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        scores.append(new_entry)
        scores.sort(key=lambda x: x['score'], reverse=True)
        scores = scores[:10]
        position = next((i + 1 for i, s in enumerate(scores) if s == new_entry), 0)
        
        with open(self._get_scores_file(game_name), 'w') as f:
            json.dump({'scores': scores}, f, indent=2)
        self.cache[game_name] = scores
        return position
    
    def get_high_score(self, game_name: str) -> int:
        scores = self.load_scores(game_name)
        return scores[0]['score'] if scores else 0

# ============== DISPLAY MANAGER ==============
class DisplayManager:
    # Risoluzioni virtuali supportate (ordine preferenza)
    VIRTUAL_RESOLUTIONS = [
        (1920, 1080),  # Full HD
        (1280, 720),   # HD Ready
    ]
    
    # Modalità scaling
    SCALE_NEAREST = 0
    SCALE_SMOOTH = 1
    SCALE_ADAPTIVE = 2
    
    # Performance profiles
    PROFILE_QUALITY = 0
    PROFILE_BALANCED = 1
    PROFILE_PERFORMANCE = 2
    
    def __init__(self, config: Config):
        self.config = config
        
        # Detect optimal virtual resolution PRIMA di inizializzare pygame.display
        self.VIRTUAL_WIDTH, self.VIRTUAL_HEIGHT = self._detect_optimal_resolution()
        print(f"[DisplayManager] Virtual resolution: {self.VIRTUAL_WIDTH}x{self.VIRTUAL_HEIGHT}")
        
        # Virtual surfaces
        self.virtual_surface = pygame.Surface((self.VIRTUAL_WIDTH, self.VIRTUAL_HEIGHT))
        self._back_buffer = pygame.Surface((self.VIRTUAL_WIDTH, self.VIRTUAL_HEIGHT))
        
        # Screen
        self.screen = None
        self._screen_buffer = None
        
        # Letterbox calculations
        self.scale = 1.0
        self.scaled_w = self.VIRTUAL_WIDTH
        self.scaled_h = self.VIRTUAL_HEIGHT
        self.offset_x = 0
        self.offset_y = 0
        
        # Scaling cache
        self._scaled_cache = {}
        self._max_cache_entries = 3
        self._scale_mode = self.SCALE_SMOOTH
        self._last_scale_time = 0
        self._scale_dirty = True
        
        # Performance tracking
        self._render_times = []
        self._max_render_samples = 120
        self._performance_profile = self.PROFILE_BALANCED
        self._adaptive_quality = True
        
        # Vsync
        self.vsync_enabled = True
        self._target_fps = 60
        
        # FPS display
        self.show_fps = False
        self.show_detailed_stats = False
        self.fps_font = None
        self.fps_history = []
        self._last_fps_update = 0
        self._fps_update_interval = 0.1
        
        # Screen shake
        self._shake_intensity = 0.0
        self._shake_duration = 0.0
        
        # Letterbox
        self.letterbox_color = (0, 0, 0)
        self.show_border = False
        self.border_color = (50, 50, 70)
        self.border_width = 2
        
        # Initialize display
        self.update_display()
    
    def _detect_optimal_resolution(self) -> tuple:
        """Detect optimal virtual resolution based on monitor"""
        try:
            # Initialize display info (non crea finestra)
            pygame.display.init()
            display_info = pygame.display.Info()
            monitor_w = display_info.current_w
            monitor_h = display_info.current_h
            
            print(f"[DisplayManager] Monitor: {monitor_w}x{monitor_h}")
            
            # Strategia: usa la risoluzione più alta che sta nel monitor
            for virt_w, virt_h in self.VIRTUAL_RESOLUTIONS:
                # Check if this resolution fits comfortably
                if monitor_w >= virt_w and monitor_h >= virt_h:
                    print(f"[DisplayManager] → Using {virt_w}x{virt_h}")
                    return (virt_w, virt_h)
            
            # Se nessuna sta perfettamente, usa la più piccola
            fallback = self.VIRTUAL_RESOLUTIONS[-1]
            print(f"[DisplayManager] → Fallback to {fallback[0]}x{fallback[1]}")
            return fallback
        
        except Exception as e:
            print(f"[DisplayManager] Detection failed: {e}")
            return (1280, 720)  # Safe fallback
    
    def _get_monitor_info(self) -> dict:
        """Get monitor information"""
        try:
            display_info = pygame.display.Info()
            modes = pygame.display.list_modes()
            
            return {
                'current_width': display_info.current_w,
                'current_height': display_info.current_h,
                'available_modes': modes if modes != -1 else [(display_info.current_w, display_info.current_h)],
                'hardware_acceleration': display_info.hw if hasattr(display_info, 'hw') else False,
            }
        except:
            return {
                'current_width': 1920,
                'current_height': 1080,
                'available_modes': [],
                'hardware_acceleration': False,
            }
    
    def update_display(self):
        """Update display mode"""
        if self.screen is not None:
            try:
                pygame.display.quit()
            except:
                pass
        
        pygame.display.init()
        
        flags = self._get_display_flags()
        
        try:
            self.screen = self._create_display(flags)
            pygame.display.set_caption("Spinner Overdrive - Arcade System")
            self._set_display_icon()
        except pygame.error as e:
            print(f"[DisplayManager] Display creation failed: {e}")
            self.screen = self._create_fallback_display()
        
        self._screen_buffer = pygame.Surface(self.config.resolution)
        self._setup_mouse()
        self.calculate_letterbox()
        self._clear_cache()
        self._initialize_fonts()
        self._render_times.clear()
        
        print(f"[DisplayManager] Display ready: {self.config.resolution[0]}x{self.config.resolution[1]}")
    
    def _get_display_flags(self) -> int:
        """Get display flags"""
        flags = 0
        if self.config.fullscreen:
            flags |= pygame.FULLSCREEN
        if hasattr(pygame, 'HWSURFACE'):
            flags |= pygame.HWSURFACE
        if hasattr(pygame, 'DOUBLEBUF'):
            flags |= pygame.DOUBLEBUF
        return flags
    
    def _create_display(self, flags: int) -> pygame.Surface:
        """Create display with vsync"""
        try:
            return pygame.display.set_mode(
                self.config.resolution,
                flags,
                vsync=1 if self.vsync_enabled else 0
            )
        except TypeError:
            return pygame.display.set_mode(self.config.resolution, flags)
    
    def _create_fallback_display(self) -> pygame.Surface:
        """Fallback display creation"""
        self.config.fullscreen = False
        
        # Prova native resolution
        try:
            if self.VIRTUAL_WIDTH == 1920:
                self.config.resolution = (1920, 1080)
            else:
                self.config.resolution = (1280, 720)
            return pygame.display.set_mode(self.config.resolution, 0)
        except:
            # Ultimate fallback
            self.config.resolution = (1280, 720)
            try:
                return pygame.display.set_mode((1280, 720), 0)
            except:
                self.config.resolution = (800, 600)
                return pygame.display.set_mode((800, 600), 0)
    
    def _set_display_icon(self):
        """Set window icon"""
        try:
            from pathlib import Path
            icon_path = Path("icon.png")
            if icon_path.exists():
                icon = pygame.image.load(str(icon_path))
                pygame.display.set_icon(icon)
        except:
            pass
    
    def _setup_mouse(self):
        """Setup mouse"""
        try:
            pygame.mouse.set_visible(False)
            pygame.event.set_grab(True)
            center_x = self.config.resolution[0] // 2
            center_y = self.config.resolution[1] // 2
            pygame.mouse.set_pos(center_x, center_y)
            pygame.mouse.get_rel()
        except:
            pass
    
    def _initialize_fonts(self):
        """Initialize fonts"""
        if self.show_fps or self.show_detailed_stats:
            try:
                self.fps_font = pygame.font.Font(None, 24)
            except:
                try:
                    self.fps_font = pygame.font.SysFont('monospace', 20)
                except:
                    self.fps_font = None
    
    def calculate_letterbox(self):
        """Calculate letterbox"""
        screen_w, screen_h = self.config.resolution
        
        scale_x = screen_w / self.VIRTUAL_WIDTH
        scale_y = screen_h / self.VIRTUAL_HEIGHT
        self.scale = min(scale_x, scale_y)
        
        # Integer scaling per pixel-perfect
        if (self._performance_profile == self.PROFILE_PERFORMANCE and 
            self._scale_mode == self.SCALE_NEAREST and self.scale >= 2.0):
            self.scale = math.floor(self.scale)
        
        self.scaled_w = int(self.VIRTUAL_WIDTH * self.scale)
        self.scaled_h = int(self.VIRTUAL_HEIGHT * self.scale)
        
        self.offset_x = (screen_w - self.scaled_w) // 2
        self.offset_y = (screen_h - self.scaled_h) // 2
        
        self._scale_dirty = True
    
    def _clear_cache(self):
        """Clear cache"""
        self._scaled_cache.clear()
        self._scale_dirty = True
    
    def set_scale_mode(self, mode: int):
        """Set scale mode"""
        if mode in (self.SCALE_NEAREST, self.SCALE_SMOOTH, self.SCALE_ADAPTIVE):
            self._scale_mode = mode
            self._clear_cache()
    
    def set_performance_profile(self, profile: int):
        """Set performance profile"""
        if profile in (self.PROFILE_QUALITY, self.PROFILE_BALANCED, self.PROFILE_PERFORMANCE):
            self._performance_profile = profile
            
            if profile == self.PROFILE_QUALITY:
                self._scale_mode = self.SCALE_SMOOTH
                self._max_cache_entries = 5
            elif profile == self.PROFILE_BALANCED:
                self._scale_mode = self.SCALE_ADAPTIVE
                self._max_cache_entries = 3
            else:
                self._scale_mode = self.SCALE_NEAREST
                self._max_cache_entries = 1
            
            self._clear_cache()
    
    def toggle_fps_display(self):
        """Toggle FPS"""
        self.show_fps = not self.show_fps
        self._initialize_fonts()
    
    def toggle_detailed_stats(self):
        """Toggle stats"""
        self.show_detailed_stats = not self.show_detailed_stats
        self._initialize_fonts()
    
    def _get_effective_scale_mode(self) -> int:
        """Get effective scale mode"""
        if self._scale_mode != self.SCALE_ADAPTIVE:
            return self._scale_mode
        
        if not self._render_times:
            return self.SCALE_SMOOTH
        
        avg_time = sum(self._render_times[-30:]) / min(len(self._render_times), 30)
        return self.SCALE_NEAREST if avg_time > 0.014 else self.SCALE_SMOOTH
    
    def _scale_surface(self) -> pygame.Surface:
        """Scale surface with cache"""
        target_size = (self.scaled_w, self.scaled_h)
        mode = self._get_effective_scale_mode()
        
        import time
        start = time.perf_counter()
        
        try:
            if mode == self.SCALE_SMOOTH:
                scaled = pygame.transform.smoothscale(self.virtual_surface, target_size)
            else:
                scaled = pygame.transform.scale(self.virtual_surface, target_size)
        except:
            scaled = pygame.transform.scale(self.virtual_surface, target_size)
        
        self._last_scale_time = time.perf_counter() - start
        return scaled
    
    def start_screen_shake(self, intensity: float, duration: float):
        """Start screen shake"""
        self._shake_intensity = intensity
        self._shake_duration = duration
    
    def _apply_screen_shake(self) -> tuple:
        """Apply screen shake"""
        if self._shake_duration <= 0:
            return (0, 0)
        
        import random
        shake_x = random.randint(-int(self._shake_intensity), int(self._shake_intensity))
        shake_y = random.randint(-int(self._shake_intensity), int(self._shake_intensity))
        return (shake_x, shake_y)
    
    def update_shake(self, dt: float):
        """Update shake"""
        if self._shake_duration > 0:
            self._shake_duration -= dt
    
    def render(self, fps: float = 0.0, dt: float = 0.0):
        """Render frame"""
        import time
        start = time.perf_counter()
        
        if dt > 0:
            self.update_shake(dt)
        
        self._screen_buffer.fill(self.letterbox_color)
        
        try:
            scaled = self._scale_surface()
            shake_x, shake_y = self._apply_screen_shake()
            self._screen_buffer.blit(scaled, (self.offset_x + shake_x, self.offset_y + shake_y))
            
            if self.show_border:
                self._draw_border(self._screen_buffer)
        except pygame.error as e:
            print(f"[DisplayManager] Render error: {e}")
            self._screen_buffer.blit(self.virtual_surface, (self.offset_x, self.offset_y))
        
        self.screen.blit(self._screen_buffer, (0, 0))
        
        if self.show_fps and self.fps_font:
            self._draw_fps(fps)
        
        if self.show_detailed_stats and self.fps_font:
            self._draw_detailed_stats(fps)
        
        try:
            pygame.display.flip()
        except:
            pygame.display.update()
        
        render_time = time.perf_counter() - start
        self._render_times.append(render_time)
        if len(self._render_times) > self._max_render_samples:
            self._render_times.pop(0)
    
    def _draw_border(self, surface: pygame.Surface):
        """Draw border"""
        rect = pygame.Rect(
            self.offset_x - self.border_width,
            self.offset_y - self.border_width,
            self.scaled_w + self.border_width * 2,
            self.scaled_h + self.border_width * 2
        )
        pygame.draw.rect(surface, self.border_color, rect, self.border_width)
    
    def _draw_fps(self, fps: float):
        """Draw FPS counter"""
        import time
        current = time.time()
        
        if current - self._last_fps_update >= self._fps_update_interval and fps > 0:
            self._last_fps_update = current
            self.fps_history.append(fps)
            if len(self.fps_history) > 60:
                self.fps_history.pop(0)
        
        if not self.fps_history:
            return
        
        avg = sum(self.fps_history) / len(self.fps_history)
        color = (0, 255, 0) if avg >= 58 else ((255, 255, 0) if avg >= 45 else (255, 0, 0))
        
        try:
            text = self.fps_font.render(f"FPS: {avg:.1f}", True, color)
            self._draw_overlay_box(text, self.offset_x + self.scaled_w - 90, self.offset_y + 10)
        except:
            pass
    
    def _draw_detailed_stats(self, fps: float):
        """Draw detailed stats"""
        if not self.fps_font or not self._render_times:
            return
        
        try:
            recent = self._render_times[-60:]
            avg = sum(recent) / len(recent)
            
            lines = [
                f"Render: {avg*1000:.2f}ms",
                f"Scale: {self._last_scale_time*1000:.2f}ms",
                f"Virtual: {self.VIRTUAL_WIDTH}x{self.VIRTUAL_HEIGHT}",
                f"Screen: {self.config.resolution[0]}x{self.config.resolution[1]}",
                f"Scale: {self.scale:.2f}x"
            ]
            
            y = self.offset_y + 50
            for line in lines:
                text = self.fps_font.render(line, True, (200, 200, 200))
                self._draw_overlay_box(text, self.offset_x + self.scaled_w - 180, y)
                y += 25
        except:
            pass
    
    def _draw_overlay_box(self, text: pygame.Surface, x: int, y: int):
        """Draw overlay box"""
        bg = pygame.Surface((text.get_width() + 10, text.get_height() + 6))
        bg.fill((0, 0, 0))
        bg.set_alpha(180)
        self.screen.blit(bg, (x - 5, y - 3))
        self.screen.blit(text, (x, y))
    
    def get_virtual_surface(self) -> pygame.Surface:
        """Get virtual surface"""
        return self.virtual_surface
    
    def get_virtual_dimensions(self) -> tuple:
        """Get virtual dimensions"""
        return (self.VIRTUAL_WIDTH, self.VIRTUAL_HEIGHT)
    
    def get_scale_factor(self) -> float:
        """Get scale factor"""
        return self.scale
    
    def take_screenshot(self, filename: str = None) -> str:
        """Take screenshot"""
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        try:
            from pathlib import Path
            Path("screenshots").mkdir(exist_ok=True)
            path = Path("screenshots") / filename
            pygame.image.save(self.virtual_surface, str(path))
            print(f"[DisplayManager] Screenshot: {path}")
            return str(path)
        except Exception as e:
            print(f"[DisplayManager] Screenshot failed: {e}")
            return None
    
    def get_info(self) -> dict:
        """Get info"""
        monitor = self._get_monitor_info()
        return {
            'virtual': (self.VIRTUAL_WIDTH, self.VIRTUAL_HEIGHT),
            'monitor': (monitor['current_width'], monitor['current_height']),
            'window': self.config.resolution,
            'scale': self.scale,
            'fullscreen': self.config.fullscreen
        }



# ============== SPINNER INPUT (FIXED) ==============
class SpinnerInput:
    def __init__(self, config: Config):
        self.config = config
        self.left_pressed = False
        self.right_pressed = False
        self.left_clicked = False
        self.right_clicked = False
        self.setup_mouse()
    
    def setup_mouse(self):
        """FIXED: Proper mouse capture for infinite rotation"""
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        pygame.mouse.set_pos(640, 360)  # Force cursor to center
        pygame.mouse.get_rel()  # Clear any existing mouse movement
    
    def ensure_mouse_hidden(self):
        """Assicura che il mouse rimanga nascosto - chiamare dopo cambio display"""
        if pygame.mouse.get_visible():
            pygame.mouse.set_visible(False)
        if not pygame.event.get_grab():
            pygame.event.set_grab(True)
    
    def update(self, events: List[pygame.event.Event]):
        # Assicura che il mouse sia sempre nascosto
        self.ensure_mouse_hidden()
        
        self.left_clicked = False
        self.right_clicked = False
        
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.left_pressed = True
                    self.left_clicked = True
                elif event.button == 3:
                    self.right_pressed = True
                    self.right_clicked = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.left_pressed = False
                elif event.button == 3:
                    self.right_pressed = False
    
    def get_rotation_delta(self) -> float:
        rel_x, _ = pygame.mouse.get_rel()
        return rel_x / (self.config.spinner_sensitivity / 50.0)
    
    def is_left_clicked(self) -> bool:
        return self.left_clicked
    
    def is_right_clicked(self) -> bool:
        return self.right_clicked
    
    def is_left_pressed(self) -> bool:
        return self.left_pressed
    
    def is_right_pressed(self) -> bool:
        return self.right_pressed
    
    def release(self):
        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)




# ============== BASE MINIGAME ==============
class MiniGame(ABC):
    def __init__(self):
        self.score = 0
        self.game_over = False
    
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        pass
    
    @abstractmethod
    def update(self, dt: float, spinner_delta: float, spinner: SpinnerInput) -> bool:
        pass
    
    @abstractmethod
    def draw(self, surface: pygame.Surface):
        pass
    
    @abstractmethod
    def reset(self):
        pass
    
    def get_score(self) -> int:
        return self.score
    
    def is_game_over(self) -> bool:
        return self.game_over

# ============== BASE STATE ==============
class GameState(ABC):
    @abstractmethod
    def update(self, dt: float, spinner_delta: float, spinner: SpinnerInput) -> Optional[str]:
        pass
    
    @abstractmethod
    def draw(self, surface: pygame.Surface):
        pass
    
    def on_enter(self):
        pass
    
    def on_exit(self):
        pass

# ============== NAME ENTRY STATE (FIXED LAYOUT) ==============
class NameEntryState(GameState):
    ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    
    def __init__(self, game_name: str, score: int, synth: SoundSynthesizer):
        self.game_name = game_name
        self.score = score
        self.synth = synth
        
        # Fonts
        self.font_title = pygame.font.Font(None, 64)
        self.font_score = pygame.font.Font(None, 52)
        self.font_letter = pygame.font.Font(None, 110)
        self.font_hint = pygame.font.Font(None, 30)
        self.font_small = pygame.font.Font(None, 24)
        
        # State
        self.letters = ['A', 'A', 'A']
        self.current_position = 0
        self.rotation_accumulator = 0.0
        self.confirmed = False
        self.player_name = ""
        
        # Animations
        self.intro_progress = 0.0
        self.intro_duration = 0.5
        self.glow_pulse = 0.0
        self.sparkles = []
        self.stars = []
        self.letter_float = [0.0, 0.0, 0.0]
        self.bg_wave_offset = 0.0
        
        # Initialize star field
        for _ in range(60):
            self.stars.append({
                'x': random.randint(0, 1280),
                'y': random.randint(0, 720),
                'speed': random.uniform(0.2, 1.0),
                'size': random.randint(1, 3),
                'brightness': random.uniform(0.3, 1.0),
                'twinkle_phase': random.uniform(0, math.pi * 2)
            })
    
    def on_enter(self):
        self.letters = ['A', 'A', 'A']
        self.current_position = 0
        self.rotation_accumulator = 0.0
        self.confirmed = False
        self.intro_progress = 0.0
        self.sparkles = []
        self.letter_float = [0.0, 0.0, 0.0]
        self._spawn_sparkles()
        self.synth.create_high_score().play()
    
    def _spawn_sparkles(self):
        """Spawn celebration sparkles"""
        for _ in range(35):
            self.sparkles.append({
                'x': random.randint(250, 1030),
                'y': random.randint(120, 480),
                'vx': random.uniform(-40, 40),
                'vy': random.uniform(-90, -25),
                'lifetime': random.uniform(2.0, 3.5),
                'max_lifetime': 3.5,
                'size': random.randint(2, 4),
                'color': random.choice([
                    (255, 255, 100), (255, 200, 100), (255, 215, 0),
                    (150, 255, 200), (200, 150, 255)
                ]),
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(-180, 180)
            })
    
    def update(self, dt: float, spinner_delta: float, spinner: SpinnerInput) -> Optional[str]:
        # Intro
        if self.intro_progress < 1.0:
            self.intro_progress = min(1.0, self.intro_progress + dt / self.intro_duration)
        
        # Animations
        self.glow_pulse += dt * 2.5
        self.bg_wave_offset += dt * 60
        
        # Floating
        for i in range(3):
            self.letter_float[i] += dt * 1.8
        
        # Stars
        for star in self.stars:
            star['x'] -= star['speed'] * dt * 15
            star['twinkle_phase'] += dt * 2
            if star['x'] < 0:
                star['x'] = 1280
                star['y'] = random.randint(0, 720)
        
        # Sparkles
        for sp in self.sparkles[:]:
            sp['x'] += sp['vx'] * dt
            sp['y'] += sp['vy'] * dt
            sp['vy'] += 180 * dt
            sp['rotation'] += sp['rotation_speed'] * dt
            sp['lifetime'] -= dt
            if sp['lifetime'] <= 0:
                self.sparkles.remove(sp)
        
        if self.confirmed:
            return None
        
        # Spinner input
        self.rotation_accumulator += spinner_delta
        THRESHOLD = 20.0
        if abs(self.rotation_accumulator) >= THRESHOLD:
            steps = int(self.rotation_accumulator / THRESHOLD)
            current_idx = self.ALPHABET.index(self.letters[self.current_position])
            new_idx = (current_idx + steps) % len(self.ALPHABET)
            self.letters[self.current_position] = self.ALPHABET[new_idx]
            self.rotation_accumulator -= steps * THRESHOLD
            self.synth.create_blip(steps).play()
        
        # Confirm
        if spinner.is_left_clicked():
            self.current_position += 1
            self.synth.create_select().play()
            if self.current_position >= 3:
                self.player_name = ''.join(self.letters).strip()
                if not self.player_name:
                    self.player_name = "AAA"
                self.confirmed = True
                return f"save_score:{self.game_name}:{self.score}:{self.player_name}"
        
        # Back
        if spinner.is_right_clicked() and self.current_position > 0:
            self.current_position -= 1
            self.synth.create_back().play()
        
        return None
    
    def draw(self, surface: pygame.Surface):
        # Background
        self._draw_background(surface)
        
        # Stars
        for star in self.stars:
            twinkle = abs(math.sin(star['twinkle_phase'])) * 0.4 + 0.6
            brightness = int(star['brightness'] * 255 * twinkle)
            color = (brightness, brightness, min(255, brightness + 50))
            if star['size'] > 1:
                pygame.draw.circle(surface, color, (int(star['x']), int(star['y'])), star['size'])
            else:
                try:
                    surface.set_at((int(star['x']), int(star['y'])), color)
                except:
                    pass
        
        # Sparkles
        for sp in self.sparkles:
            alpha = int(255 * (sp['lifetime'] / sp['max_lifetime']))
            self._draw_sparkle(surface, sp['x'], sp['y'], sp['size'], sp['color'], alpha, sp['rotation'])
        
        ease = self._ease_out_cubic(self.intro_progress)
        
        # Title
        title_y = 50 + (1 - ease) * -40
        self._draw_glowing_title(surface, "NEW HIGH SCORE!", title_y, (255, 215, 0))
        
        # Game name
        game_y = 130
        game_name = self.font_small.render(self.game_name.upper(), True, (150, 200, 255))
        surface.blit(game_name, (640 - game_name.get_width()//2, game_y))
        
        # Score
        score_y = 170
        score_label = self.font_small.render("SCORE", True, (150, 180, 200))
        score_text = self.font_score.render(f"{self.score:,}", True, (150, 255, 200))
        surface.blit(score_label, (640 - score_label.get_width()//2, score_y))
        surface.blit(score_text, (640 - score_text.get_width()//2, score_y + 26))
        
        # Line
        line_y = 245
        line_width = int(700 * ease)
        pygame.draw.line(surface, (100, 120, 180), 
                        (640 - line_width//2, line_y), 
                        (640 + line_width//2, line_y), 2)
        
        # Instruction
        inst_y = 270
        inst = self.font_small.render("Enter Your Name", True, (200, 220, 240))
        surface.blit(inst, (640 - inst.get_width()//2, inst_y))
        
        # Letters
        letter_y = 350
        self._draw_letters(surface, letter_y, ease)
        
        # Hints
        hints_y = 640
        self._draw_hints(surface, hints_y)
    
    def _draw_background(self, surface: pygame.Surface):
        """Background gradient animato"""
        for y in range(720):
            factor = y / 720
            wave = math.sin(self.bg_wave_offset * 0.015 + factor * 4) * 10
            r = int(15 + wave + factor * 5)
            g = int(15 + wave + factor * 8)
            b = int(35 + wave + factor * 15)
            pygame.draw.line(surface, (r, g, b), (0, y), (1280, y))
    
    def _draw_glowing_title(self, surface: pygame.Surface, text: str, y: float, color: tuple):
        """Title con glow"""
        glow_intensity = abs(math.sin(self.glow_pulse)) * 50 + 200
        
        # Glow
        for blur in range(6, 0, -2):
            alpha = int(35 - blur * 4)
            glow_surf = self.font_title.render(text, True, (int(glow_intensity), int(glow_intensity * 0.8), 0))
            glow_surf.set_alpha(alpha)
            for offset in [(blur, 0), (-blur, 0), (0, blur), (0, -blur)]:
                surface.blit(glow_surf, (640 - glow_surf.get_width()//2 + offset[0], int(y) + offset[1]))
        
        # Shadow
        shadow = self.font_title.render(text, True, (20, 20, 0))
        surface.blit(shadow, (640 - shadow.get_width()//2 + 2, int(y) + 2))
        
        # Main
        title = self.font_title.render(text, True, color)
        surface.blit(title, (640 - title.get_width()//2, int(y)))
    
    def _draw_sparkle(self, surface: pygame.Surface, x: float, y: float, size: int, 
                      color: tuple, alpha: int, rotation: float):
        """Star sparkle"""
        sparkle_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
        center = size * 2
        
        points = []
        for i in range(8):
            angle = math.radians(rotation + i * 45)
            radius = size * 1.5 if i % 2 == 0 else size * 0.7
            px = center + math.cos(angle) * radius
            py = center + math.sin(angle) * radius
            points.append((px, py))
        
        pygame.draw.polygon(sparkle_surf, (*color, alpha), points)
        pygame.draw.circle(sparkle_surf, (*color, alpha), (center, center), size // 2)
        
        surface.blit(sparkle_surf, (x - center, y - center))
    
    def _draw_letters(self, surface: pygame.Surface, base_y: int, intro_ease: float):
        """Letters - stile arcade compatto"""
        BOX_SIZE = 140
        GAP = 30  # Gap ridotto per vicinanza
        total_width = BOX_SIZE * 3 + GAP * 2
        start_x = (1280 - total_width) // 2
        
        for i, letter in enumerate(self.letters):
            is_current = i == self.current_position
            is_past = i < self.current_position
            
            # Float
            float_offset = math.sin(self.letter_float[i] + i * 1.5) * 7
            
            box_x = start_x + (i * (BOX_SIZE + GAP))
            box_y = base_y + float_offset
            
            # Intro slide
            intro_delay = i * 0.18
            letter_intro = max(0, min(1, (intro_ease - intro_delay) / 0.5))
            intro_offset = (1 - letter_intro) * -120
            
            self._draw_letter_box(surface, box_x, int(box_y + intro_offset), BOX_SIZE, 
                                 letter, is_current, is_past, letter_intro, i)
    
    def _draw_letter_box(self, surface: pygame.Surface, x: int, y: int, 
                         size: int, letter: str, is_current: bool, 
                         is_past: bool, alpha: float, index: int):
        """Single letter box - stile fumetto arcade"""
        
        # === OUTER GLOW (solo current) ===
        if is_current:
            glow_size = int(10 + math.sin(self.glow_pulse * 2) * 5)
            for i in range(glow_size, 0, -2):
                glow_alpha = int((60 - i * 4) * alpha)
                glow_surf = pygame.Surface((size + i * 2, size + i * 2), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (255, 215, 0, glow_alpha), (0, 0, size + i * 2, size + i * 2), 0, 8)
                surface.blit(glow_surf, (x - i, y - i))
        
        # === BOX PRINCIPALE ===
        box_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Colori arcade vivaci
        if is_current:
            bg_color = (70, 60, 20)
            border_outer = (255, 215, 0)     # Gold
            border_inner = (255, 255, 150)   # Light gold
            border_width = 5
        elif is_past:
            bg_color = (20, 70, 50)
            border_outer = (0, 255, 150)     # Bright green
            border_inner = (150, 255, 200)   # Light green
            border_width = 5
        else:
            bg_color = (25, 35, 55)
            border_outer = (100, 120, 180)   # Blue
            border_inner = (150, 170, 220)   # Light blue
            border_width = 4
        
        # Background solido
        pygame.draw.rect(box_surf, bg_color, (0, 0, size, size), 0, 6)
        
        # Inner highlight (stile fumetto)
        highlight_rect = pygame.Rect(6, 6, size - 12, size - 12)
        pygame.draw.rect(box_surf, (*bg_color, 80), highlight_rect, 0, 4)
        
        # === BORDO STILE FUMETTO (doppio) ===
        # Bordo esterno spesso
        pygame.draw.rect(box_surf, border_outer, (0, 0, size, size), border_width, 6)
        
        # Bordo interno chiaro (comic style)
        inner_offset = border_width - 1
        inner_size = size - inner_offset * 2
        pygame.draw.rect(box_surf, border_inner, (inner_offset, inner_offset, inner_size, inner_size), 2, 4)
        
        # === ANGOLI RINFORZATI (stile arcade) ===
        corner_size = 15
        corner_color = border_outer
        
        # Angoli esterni decorativi
        corners = [
            (3, 3), (size - corner_size - 3, 3),
            (3, size - corner_size - 3), (size - corner_size - 3, size - corner_size - 3)
        ]
        
        for cx, cy in corners:
            # Piccolo quadrato negli angoli
            pygame.draw.rect(box_surf, corner_color, (cx, cy, corner_size, corner_size), 0, 2)
            pygame.draw.rect(box_surf, border_inner, (cx + 2, cy + 2, corner_size - 4, corner_size - 4), 1, 1)
        
        # Apply alpha
        box_surf.set_alpha(int(255 * alpha))
        surface.blit(box_surf, (x, y))
        
        # === LETTERA ===
        if is_current:
            letter_color = (255, 255, 240)
        elif is_past:
            letter_color = (220, 255, 240)
        else:
            letter_color = (180, 200, 230)
        
        # Shadow spesso (fumetto)
        shadow_offset = 3
        shadow = self.font_letter.render(letter, True, (0, 0, 0))
        shadow_rect = shadow.get_rect(center=(x + size // 2 + shadow_offset, y + size // 2 + shadow_offset))
        shadow.set_alpha(int(200 * alpha))
        surface.blit(shadow, shadow_rect)
        
        # Outline scuro
        outline_color = (30, 30, 40)
        for ox, oy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            outline = self.font_letter.render(letter, True, outline_color)
            outline_rect = outline.get_rect(center=(x + size // 2 + ox, y + size // 2 + oy))
            outline.set_alpha(int(180 * alpha))
            surface.blit(outline, outline_rect)
        
        # Lettera principale
        letter_text = self.font_letter.render(letter, True, letter_color)
        letter_rect = letter_text.get_rect(center=(x + size // 2, y + size // 2))
        letter_text.set_alpha(int(255 * alpha))
        surface.blit(letter_text, letter_rect)
        
        # === ARROW (solo current) ===
        if is_current and alpha > 0.7:
            arrow_y = y - 40
            arrow_x = x + size // 2
            bounce = math.sin(self.glow_pulse * 3) * 6
            
            # Arrow grossa stile arcade
            points = [
                (arrow_x, arrow_y + bounce),
                (arrow_x - 16, arrow_y - 16 + bounce),
                (arrow_x + 16, arrow_y - 16 + bounce)
            ]
            
            # Shadow arrow
            shadow_points = [(p[0] + 2, p[1] + 2) for p in points]
            pygame.draw.polygon(surface, (0, 0, 0, 100), shadow_points)
            
            # Glow arrow
            for offset in range(4, 0, -1):
                glow_alpha = 50 - offset * 10
                glow_points = [
                    (arrow_x, arrow_y + bounce),
                    (arrow_x - 16 - offset, arrow_y - 16 - offset + bounce),
                    (arrow_x + 16 + offset, arrow_y - 16 - offset + bounce)
                ]
                arrow_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
                pygame.draw.polygon(arrow_surf, (255, 255, 100, glow_alpha), 
                                  [(p[0] - arrow_x + 20, p[1] - arrow_y + 20) for p in glow_points])
                surface.blit(arrow_surf, (arrow_x - 20, arrow_y - 20))
            
            # Solid arrow
            pygame.draw.polygon(surface, (255, 255, 150), points)
            
            # Outline arrow (fumetto)
            pygame.draw.polygon(surface, (255, 215, 0), points, 3)
    
    def _draw_hints(self, surface: pygame.Surface, y: int):
        """Hints pulsanti"""
        if self.confirmed:
            saving_alpha = int(220 + abs(math.sin(self.glow_pulse * 1.8)) * 35)
            saving = self.font_hint.render("Saving your record...", True, (255, 230, 100))
            saving.set_alpha(saving_alpha)
            surface.blit(saving, (640 - saving.get_width() // 2, y))
            return
        
        hint_alpha = int(190 + abs(math.sin(self.glow_pulse * 0.7)) * 65)
        
        if self.current_position > 0:
            hint_text = "SPIN: Change  •  LEFT: Confirm  •  RIGHT: Back"
        else:
            hint_text = "SPIN: Change  •  LEFT: Confirm"
        
        hint = self.font_hint.render(hint_text, True, (100, 255, 100))
        hint.set_alpha(hint_alpha)
        surface.blit(hint, (640 - hint.get_width() // 2, y))
    
    def _ease_out_cubic(self, t: float) -> float:
        """Cubic ease"""
        return 1 - pow(1 - t, 3)





# ============== HIGH SCORE STATE ==============
class HighScoreState(GameState):
    def __init__(self, game_name: str, high_score_mgr: HighScoreManager, synth: SoundSynthesizer):
        self.game_name = game_name
        self.high_score_mgr = high_score_mgr
        self.synth = synth
        self.scores = []
        
        # Fonts
        self.font_title = pygame.font.Font(None, 70)
        self.font_header = pygame.font.Font(None, 45)
        self.font_score = pygame.font.Font(None, 34)
        self.font_hint = pygame.font.Font(None, 32)
        
        # Animations
        self.intro_progress = 0.0
        self.intro_duration = 0.8
        self.glow_pulse = 0.0
        self.wave_offset = 0.0
        self.sparkles = []
        self.stars = []
        
        # Row animations
        self.row_animations = []
        
        # Initialize star field
        for _ in range(80):
            self.stars.append({
                'x': random.randint(0, 1280),
                'y': random.randint(0, 720),
                'speed': random.uniform(0.2, 1.0),
                'size': random.randint(1, 3),
                'brightness': random.uniform(0.3, 1.0),
                'twinkle_phase': random.uniform(0, math.pi * 2)
            })
    
    def on_enter(self):
        self.scores = self.high_score_mgr.load_scores(self.game_name)
        self.intro_progress = 0.0
        self.glow_pulse = 0.0
        self.wave_offset = 0.0
        self.sparkles = []
        
        # Initialize row animations with stagger
        self.row_animations = []
        for i in range(len(self.scores)):
            self.row_animations.append({
                'delay': i * 0.08,
                'progress': 0.0,
                'y_offset': 100
            })
        
        # Spawn celebration sparkles for top 3
        if len(self.scores) > 0:
            self._spawn_celebration_sparkles()
    
    def _spawn_celebration_sparkles(self):
        """Spawn sparkles for top 3 scores"""
        positions = [
            (350, 250),
            (580, 250),
            (800, 250)
        ]
        
        for i, (base_x, base_y) in enumerate(positions[:min(3, len(self.scores))]):
            for _ in range(15):
                self.sparkles.append({
                    'x': base_x + random.randint(-50, 50),
                    'y': base_y + random.randint(-30, 30),
                    'vx': random.uniform(-30, 30),
                    'vy': random.uniform(-80, -20),
                    'lifetime': random.uniform(2.0, 4.0),
                    'max_lifetime': 4.0,
                    'size': random.randint(2, 4),
                    'color': [(255, 215, 0), (255, 255, 100), (255, 200, 100)][i],
                    'rotation': random.uniform(0, 360),
                    'rotation_speed': random.uniform(-180, 180)
                })
    
    def update(self, dt: float, spinner_delta: float, spinner: SpinnerInput) -> Optional[str]:
        # Intro animation
        if self.intro_progress < 1.0:
            self.intro_progress = min(1.0, self.intro_progress + dt / self.intro_duration)
        
        # Pulse and waves
        self.glow_pulse += dt * 2.5
        self.wave_offset += dt * 60
        
        # Update stars
        for star in self.stars:
            star['x'] -= star['speed'] * dt * 15
            star['twinkle_phase'] += dt * 2
            if star['x'] < 0:
                star['x'] = 1280
                star['y'] = random.randint(0, 720)
        
        # Update sparkles
        for sp in self.sparkles[:]:
            sp['x'] += sp['vx'] * dt
            sp['y'] += sp['vy'] * dt
            sp['vy'] += 150 * dt
            sp['rotation'] += sp['rotation_speed'] * dt
            sp['lifetime'] -= dt
            if sp['lifetime'] <= 0:
                self.sparkles.remove(sp)
        
        # Update row animations
        for anim in self.row_animations:
            if anim['delay'] > 0:
                anim['delay'] -= dt
            else:
                if anim['progress'] < 1.0:
                    anim['progress'] = min(1.0, anim['progress'] + dt / 0.4)
                    # Ease out back
                    t = anim['progress']
                    ease = 1 + (2.70158 + 1) * pow(t - 1, 3) + 2.70158 * pow(t - 1, 2)
                    anim['y_offset'] = 100 * (1 - ease)
        
        # Exit
        if spinner.is_left_clicked() or spinner.is_right_clicked():
            self.synth.create_back().play()
            return "main_menu"
        
        return None
    
    def draw(self, surface: pygame.Surface):
        # === ANIMATED BACKGROUND ===
        self._draw_background(surface)
        
        # === STARS ===
        for star in self.stars:
            twinkle = abs(math.sin(star['twinkle_phase'])) * 0.4 + 0.6
            brightness = int(star['brightness'] * 255 * twinkle)
            color = (brightness, brightness, min(255, brightness + 50))
            if star['size'] > 1:
                pygame.draw.circle(surface, color, (int(star['x']), int(star['y'])), star['size'])
            else:
                try:
                    surface.set_at((int(star['x']), int(star['y'])), color)
                except:
                    pass
        
        # === SPARKLES ===
        for sp in self.sparkles:
            alpha = int(255 * (sp['lifetime'] / sp['max_lifetime']))
            self._draw_sparkle(surface, sp['x'], sp['y'], sp['size'], sp['color'], alpha, sp['rotation'])
        
        intro_ease = self._ease_out_cubic(self.intro_progress)
        
        # === TITLE with glow ===
        title_y = 30 + (1 - intro_ease) * -50
        self._draw_glowing_title(surface, "HIGH SCORES", title_y, (255, 215, 0))
        
        # === GAME NAME with underline ===
        game_y = 110
        game_title = self.font_header.render(self.game_name, True, (150, 200, 255))
        game_shadow = self.font_header.render(self.game_name, True, (0, 0, 50))
        surface.blit(game_shadow, (640 - game_title.get_width()//2 + 2, game_y + 2))
        surface.blit(game_title, (640 - game_title.get_width()//2, game_y))
        
        # Animated underline
        underline_width = int(game_title.get_width() * intro_ease)
        underline_y = game_y + 50
        pygame.draw.line(surface, (100, 150, 255), 
                        (640 - underline_width//2, underline_y),
                        (640 + underline_width//2, underline_y), 3)
        
        # === TABLE HEADER ===
        header_y = 190
        self._draw_table_header(surface, header_y, intro_ease)
        
        # === DECORATIVE LINE ===
        line_y = header_y + 45
        line_width = int(1100 * intro_ease)
        pygame.draw.line(surface, (100, 120, 180), 
                        (90, line_y), (90 + line_width, line_y), 2)
        
        # === SCORE ROWS ===
        base_y = 250
        self._draw_score_rows(surface, base_y)
        
        # === HINT ===
        hint_y = 680
        hint_alpha = int(255 * abs(math.sin(self.glow_pulse * 0.5)))
        hint = self.font_hint.render("Click to return", True, (100, 255, 100))
        hint.set_alpha(hint_alpha)
        surface.blit(hint, (640 - hint.get_width()//2, hint_y))
        
        # === NO SCORES MESSAGE ===
        if len(self.scores) == 0:
            self._draw_empty_state(surface)
    
    def _draw_background(self, surface: pygame.Surface):
        """Animated gradient background"""
        for y in range(720):
            factor = y / 720
            wave = math.sin(self.wave_offset * 0.015 + factor * 4) * 10
            r = int(15 + wave + factor * 5)
            g = int(15 + wave + factor * 8)
            b = int(35 + wave + factor * 15)
            pygame.draw.line(surface, (r, g, b), (0, y), (1280, y))
    
    def _draw_glowing_title(self, surface: pygame.Surface, text: str, y: float, color: tuple):
        """Draw title with pulsing glow"""
        glow_intensity = abs(math.sin(self.glow_pulse)) * 60 + 195
        
        # Glow layers
        for blur in range(8, 0, -2):
            alpha = int(40 - blur * 3)
            glow_surf = self.font_title.render(text, True, (int(glow_intensity), int(glow_intensity * 0.8), 0))
            glow_surf.set_alpha(alpha)
            for offset in [(blur, 0), (-blur, 0), (0, blur), (0, -blur)]:
                surface.blit(glow_surf, (640 - glow_surf.get_width()//2 + offset[0], int(y) + offset[1]))
        
        # Shadow
        shadow = self.font_title.render(text, True, (20, 20, 0))
        surface.blit(shadow, (640 - shadow.get_width()//2 + 3, int(y) + 3))
        
        # Main text
        title = self.font_title.render(text, True, color)
        surface.blit(title, (640 - title.get_width()//2, int(y)))
    
    def _draw_table_header(self, surface: pygame.Surface, y: int, intro_ease: float):
        """Draw table header - PULITO SENZA BORDI E SFONDI"""
        headers = [
            ("RANK", 120),
            ("PLAYER", 370),
            ("SCORE", 650),
            ("DATE", 920)
        ]
        
        for i, (text, x) in enumerate(headers):
            delay_factor = 1.0 - (i * 0.1)
            alpha = int(255 * min(1.0, intro_ease / delay_factor))
            
            # Text pulito senza background
            header_text = self.font_score.render(text, True, (200, 220, 255))
            header_text.set_alpha(alpha)
            surface.blit(header_text, (x, y))
    
    def _draw_score_rows(self, surface: pygame.Surface, base_y: int):
        """Draw score rows - SENZA TREMOLIO"""
        ROW_HEIGHT = 42
        
        for i, entry in enumerate(self.scores):
            if i >= len(self.row_animations):
                continue
            
            anim = self.row_animations[i]
            if anim['progress'] == 0.0:
                continue
            
            y = base_y + i * ROW_HEIGHT + anim['y_offset']
            
            # Row alpha based on animation
            alpha = int(255 * anim['progress'])
            
            # Posizione fissa, nessun bounce
            final_y = y
            
            # Medal/trophy for top 3
            if i < 3:
                self._draw_medal(surface, 85, final_y + 15, i, alpha)
            
            # Rank color and styling
            if i == 0:
                color = (255, 215, 0)  # Gold
                rank_bg_color = (255, 215, 0, 80)
            elif i == 1:
                color = (192, 192, 192)  # Silver
                rank_bg_color = (192, 192, 192, 60)
            elif i == 2:
                color = (205, 127, 50)  # Bronze
                rank_bg_color = (205, 127, 50, 60)
            else:
                color = (180, 180, 200)
                rank_bg_color = (60, 70, 100, 40)
            
            # Row background with highlight for top 3
            if i < 3:
                row_bg = pygame.Surface((1100, 38), pygame.SRCALPHA)
                row_bg.fill(rank_bg_color)
                pygame.draw.rect(row_bg, (*color, 100), (0, 0, 1100, 38), 2, 8)
                row_bg.set_alpha(alpha)
                surface.blit(row_bg, (90, final_y - 3))
            
            # === COLONNE ALLINEATE ===
            # Rank
            rank_text = self.font_score.render(f"#{i+1}", True, color)
            rank_text.set_alpha(alpha)
            surface.blit(rank_text, (120, final_y))
            
            # Player name
            player_text = self.font_score.render(entry['player'], True, color if i < 3 else (220, 220, 240))
            player_text.set_alpha(alpha)
            surface.blit(player_text, (370, final_y))
            
            # Score with formatting
            score_str = f"{entry['score']:,}"
            score_text = self.font_score.render(score_str, True, (150, 255, 200) if i < 3 else (200, 200, 220))
            score_text.set_alpha(alpha)
            surface.blit(score_text, (650, final_y))
            
            # Date
            date_text = self.font_score.render(entry['date'], True, (150, 170, 200))
            date_text.set_alpha(alpha)
            surface.blit(date_text, (920, final_y))
    
    def _draw_medal(self, surface: pygame.Surface, x: int, y: int, rank: int, alpha: int):
        """Draw medal/trophy for top 3"""
        colors = [
            (255, 215, 0),   # Gold
            (192, 192, 192), # Silver
            (205, 127, 50)   # Bronze
        ]
        
        color = colors[rank]
        size = 16
        
        # Medal circle
        medal_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(medal_surf, color, (size, size), size)
        pygame.draw.circle(medal_surf, (255, 255, 255), (size, size), size, 3)
        
        # Rank number on medal
        font_small = pygame.font.Font(None, 22)
        rank_num = font_small.render(str(rank + 1), True, (50, 50, 50))
        medal_surf.blit(rank_num, (size - rank_num.get_width()//2, size - rank_num.get_height()//2))
        
        # Crown for first place
        if rank == 0:
            crown_points = [
                (size, size - 18),
                (size - 7, size - 11),
                (size - 4, size - 16),
                (size, size - 13),
                (size + 4, size - 16),
                (size + 7, size - 11)
            ]
            pygame.draw.polygon(medal_surf, (255, 223, 0), crown_points)
            pygame.draw.polygon(medal_surf, (255, 255, 100), crown_points, 2)
        
        medal_surf.set_alpha(alpha)
        surface.blit(medal_surf, (x - size, y - size))
    
    def _draw_sparkle(self, surface: pygame.Surface, x: float, y: float, size: int, 
                      color: tuple, alpha: int, rotation: float):
        """Draw star-shaped sparkle"""
        sparkle_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
        center = size * 2
        
        # Star shape with rotation
        points = []
        for i in range(8):
            angle = math.radians(rotation + i * 45)
            radius = size * 1.5 if i % 2 == 0 else size * 0.7
            px = center + math.cos(angle) * radius
            py = center + math.sin(angle) * radius
            points.append((px, py))
        
        pygame.draw.polygon(sparkle_surf, (*color, alpha), points)
        
        # Center glow
        pygame.draw.circle(sparkle_surf, (*color, alpha), (center, center), size // 2)
        
        surface.blit(sparkle_surf, (x - center, y - center))
    
    def _draw_empty_state(self, surface: pygame.Surface):
        """Draw message when no scores exist"""
        empty_y = 350
        
        # Icon
        icon_size = 60
        pygame.draw.circle(surface, (100, 100, 120), (640, empty_y), icon_size, 4)
        pygame.draw.line(surface, (100, 100, 120), (640, empty_y - 20), (640, empty_y + 5), 6)
        pygame.draw.circle(surface, (100, 100, 120), (640, empty_y + 15), 5)
        
        # Message
        msg = self.font_header.render("No high scores yet!", True, (150, 150, 170))
        surface.blit(msg, (640 - msg.get_width()//2, empty_y + 80))
        
        hint = self.font_score.render("Be the first to set a record!", True, (120, 140, 160))
        surface.blit(hint, (640 - hint.get_width()//2, empty_y + 130))
    
    def _ease_out_cubic(self, t: float) -> float:
        """Cubic ease out"""
        return 1 - pow(1 - t, 3)


# ============== MAIN MENU STATE (FIXED RECORD POSITION) ==============



class MainMenuState(GameState):
    def __init__(self, games: List[MiniGame], high_score_mgr: HighScoreManager, synth: SoundSynthesizer):
        self.games = games
        self.high_score_mgr = high_score_mgr
        self.synth = synth
        self.background = AnimatedBackground()
        self.carousel = MenuCarousel()
        
        for game in games:
            self.carousel.add_item(game.get_name(), game.get_description())
        self.carousel.add_item("Settings", "Configure sensitivity and display")
        self.carousel.add_item("Exit", "Quit the system")
        
        # Load logo PNG (fallback to text if not found)
        self.logo_image = None
        try:
            self.logo_image = pygame.image.load("spinner_overdose_logo.png").convert_alpha()
            # ULTERIORMENTE RIDOTTO - da 438 a 350 pixel (circa 42% più piccolo dell'originale)
            logo_width = 350
            logo_height = int(self.logo_image.get_height() * (logo_width / self.logo_image.get_width()))
            self.logo_image = pygame.transform.smoothscale(self.logo_image, (logo_width, logo_height))
        except:
            print("Warning: spinner_overdose_logo.png not found, using text logo")
        
        self.font_logo = pygame.font.Font(None, 70)  # Ridotto ulteriormente
        self.font_info = pygame.font.Font(None, 46)
        self.font_hint = pygame.font.Font(None, 26)
        self.font_counter = pygame.font.Font(None, 36)
        self.rotation_accumulator = 0.0
        self.selection_cooldown = 0.0
        self.pulse_timer = 0.0
    
    def update(self, dt: float, spinner_delta: float, spinner: SpinnerInput) -> Optional[str]:
        if self.selection_cooldown > 0:
            self.selection_cooldown -= dt
        self.pulse_timer += dt * 2.0
        self.background.update(dt)
        self.carousel.update(dt)
        
        if not self.carousel.is_transitioning:
            self.rotation_accumulator += spinner_delta
            THRESHOLD = 45.0
            if abs(self.rotation_accumulator) >= THRESHOLD:
                steps = int(self.rotation_accumulator / THRESHOLD)
                direction = 1 if steps > 0 else -1
                self.carousel.navigate(direction)
                self.rotation_accumulator -= steps * THRESHOLD
                self.selection_cooldown = 0.2
                self.synth.create_blip(direction).play()
        
        if spinner.is_left_clicked() and self.selection_cooldown <= 0:
            self.synth.create_select().play()
            current = self.carousel.get_current_index()
            if current < len(self.games):
                return f"game:{current}"
            elif current == len(self.games):
                return "config"
            else:
                return "exit"
        
        if spinner.is_right_clicked():
            current = self.carousel.get_current_index()
            if current < len(self.games):
                self.synth.create_back().play()
                return f"view_scores:{self.games[current].get_name()}"
        return None
    
    def draw(self, surface: pygame.Surface):
        self.background.draw(surface)
        
        # === LOGO RIDOTTO (350px) ===
        logo_y = 30
        
        if self.logo_image:
            logo_x = 620 - self.logo_image.get_width() // 2
            surface.blit(self.logo_image, (logo_x, logo_y))
        else:
            logo_text = "SPINNER OVERDOSE"
            logo = self.font_logo.render(logo_text, True, (255, 230, 0))
            shadow = self.font_logo.render(logo_text, True, (0, 0, 0))
            surface.blit(shadow, (640 - logo.get_width()//2 + 3, logo_y + 3))
            surface.blit(logo, (640 - logo.get_width()//2, logo_y))
        
        # === CAROUSEL ===
        self.carousel.draw(surface, 180, 120)
                                
        # === RECORD SCORE (stile arcade - glow ridotto) ===
        current_idx = self.carousel.get_current_index()
        if current_idx < len(self.games):
            high_score = self.high_score_mgr.get_high_score(self.games[current_idx].get_name())
            
            # Animazioni
            pulse = abs(math.sin(self.pulse_timer * 1.2)) * 0.15 + 0.85
            glow_pulse = abs(math.sin(self.pulse_timer * 2.0)) * 0.2 + 0.8
            float_offset = math.sin(self.pulse_timer * 1.5) * 2
            
            # Record text
            score_text = self.font_info.render(f"RECORD: {high_score:,}", True, (255, 255, 240))
            
            # Box dimensions
            box_width = score_text.get_width() + 30
            box_height = 55
            box_x = 640 - box_width // 2
            box_y = 625 + float_offset
            
            # === GLOW ESTERNO RIDOTTO ===
            glow_size = int(4 + glow_pulse * 2)
            for i in range(glow_size, 0, -1):
                glow_alpha = int((30 - i * 5) * glow_pulse)
                glow_surf = pygame.Surface((box_width + i * 2, box_height + i * 2), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (255, 215, 0, glow_alpha), (0, 0, box_width + i * 2, box_height + i * 2), 0, 10)
                surface.blit(glow_surf, (box_x - i, box_y - i))
            
            # === BOX PRINCIPALE ===
            score_box = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
            
            # Background
            bg_color = (45, 40, 25)
            pygame.draw.rect(score_box, bg_color, (0, 0, box_width, box_height), 0, 10)
            
            # Inner highlight subtile
            highlight_alpha = int(30 + glow_pulse * 10)
            highlight_rect = pygame.Rect(6, 6, box_width - 12, box_height - 12)
            pygame.draw.rect(score_box, (80, 70, 40, highlight_alpha), highlight_rect, 0, 8)
            
            # === BORDO DOPPIO ===
            # Outer border
            border_intensity = pulse
            border_color = (
                int(255 * border_intensity),
                int(215 * border_intensity),
                int(50)
            )
            pygame.draw.rect(score_box, border_color, (0, 0, box_width, box_height), 5, 10)
            
            # Inner border
            inner_intensity = 0.85 + glow_pulse * 0.15
            inner_color = (
                int(255 * inner_intensity),
                int(255 * inner_intensity),
                int(150 * inner_intensity)
            )
            pygame.draw.rect(score_box, inner_color, (4, 4, box_width - 8, box_height - 8), 2, 8)
            
            # === ANGOLI DECORATIVI ===
            corner_size = 12
            corners = [
                (3, 3), (box_width - corner_size - 3, 3),
                (3, box_height - corner_size - 3), (box_width - corner_size - 3, box_height - corner_size - 3)
            ]
            
            for cx, cy in corners:
                pygame.draw.rect(score_box, border_color, (cx, cy, corner_size, corner_size), 0, 3)
                pygame.draw.rect(score_box, inner_color, (cx + 2, cy + 2, corner_size - 4, corner_size - 4), 1, 2)
            
            # Blit box
            surface.blit(score_box, (box_x, box_y))
            
            # === TESTO CON OUTLINE ===
            text_x = box_x + box_width // 2
            text_y = box_y + box_height // 2
            
            # Shadow
            shadow_offset = 2
            shadow_text = self.font_info.render(f"RECORD: {high_score:,}", True, (0, 0, 0))
            shadow_rect = shadow_text.get_rect(center=(text_x + shadow_offset, text_y + shadow_offset))
            shadow_text.set_alpha(int(180 + pulse * 30))
            surface.blit(shadow_text, shadow_rect)
            
            # Outline 8-direction
            outline_color = (30, 25, 15)
            for ox, oy in [(-1, -1), (1, -1), (-1, 1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]:
                outline = self.font_info.render(f"RECORD: {high_score:,}", True, outline_color)
                outline_rect = outline.get_rect(center=(text_x + ox, text_y + oy))
                outline.set_alpha(200)
                surface.blit(outline, outline_rect)
            
            # Main text
            text_intensity = pulse
            text_color = (
                int(255 * text_intensity),
                int(255 * text_intensity),
                int(240 * text_intensity)
            )
            final_text = self.font_info.render(f"RECORD: {high_score:,}", True, text_color)
            final_rect = final_text.get_rect(center=(text_x, text_y))
            surface.blit(final_text, final_rect)


        
        # === COUNTER ===
        counter_text = f"{current_idx + 1}/{self.carousel.get_item_count()}"
        counter_bg = pygame.Surface((80, 45), pygame.SRCALPHA)
        pygame.draw.rect(counter_bg, (0, 0, 0, 150), (0, 0, 80, 45), 0, 8)
        pygame.draw.rect(counter_bg, (255, 200, 0), (0, 0, 80, 45), 3, 8)
        surface.blit(counter_bg, (1180, 20))
        counter = self.font_counter.render(counter_text, True, (255, 255, 255))
        surface.blit(counter, (1220 - counter.get_width()//2, 32))
        
        # === ARROWS ===
        arrow_y = 360
        
        left_points = [(35, arrow_y), (60, arrow_y - 25), (60, arrow_y + 25)]
        pygame.draw.polygon(surface, (0, 0, 0), [(p[0]+2, p[1]+2) for p in left_points])
        pygame.draw.polygon(surface, (100, 150, 255), left_points)
        pygame.draw.polygon(surface, (255, 255, 255), left_points, 3)
        
        right_points = [(1245, arrow_y), (1220, arrow_y - 25), (1220, arrow_y + 25)]
        pygame.draw.polygon(surface, (0, 0, 0), [(p[0]+2, p[1]+2) for p in right_points])
        pygame.draw.polygon(surface, (100, 150, 255), right_points)
        pygame.draw.polygon(surface, (255, 255, 255), right_points, 3)
        
        # === HINTS ===
        hints = self.font_hint.render("SPINNER: Navigate  •  LEFT: Select  •  RIGHT: High Scores", True, (180, 230, 180))
        surface.blit(hints, (640 - hints.get_width()//2, 695))




# ============== CONFIG MENU STATE ==============
class ConfigMenuState(GameState):
    def __init__(self, config: Config, display: DisplayManager, synth: SoundSynthesizer):
        self.config = config
        self.display = display
        self.synth = synth
        self.background = AnimatedBackground()  # Aggiungi lo sfondo animato
        self.font_title = pygame.font.Font(None, 70)
        self.font_item = pygame.font.Font(None, 46)
        self.font_item_selected = pygame.font.Font(None, 56)
        self.font_hint = pygame.font.Font(None, 30)
        self.font_indicator = pygame.font.Font(None, 32)
        self.selected = 0
        self.resolutions = [(1280, 720), (1920, 1080)]
        self.rotation_accumulator = 0.0
        self.adjusting = False
        self.adjustment_cooldown = 0.0
        self.needs_display_update = False
        self.last_selected = -1
    
    def update(self, dt: float, spinner_delta: float, spinner: SpinnerInput) -> Optional[str]:
        # Aggiorna lo sfondo animato
        self.background.update(dt)
        
        if self.adjustment_cooldown > 0:
            self.adjustment_cooldown -= dt
        if self.needs_display_update:
            self.display.update_display()
            self.needs_display_update = False
            self.adjustment_cooldown = 0.3
        
        if not self.adjusting:
            self.rotation_accumulator += spinner_delta
            THRESHOLD = 40.0
            if abs(self.rotation_accumulator) >= THRESHOLD:
                steps = int(self.rotation_accumulator / THRESHOLD)
                self.selected = (self.selected + steps) % 3
                self.rotation_accumulator -= steps * THRESHOLD
                if self.selected != self.last_selected:
                    self.synth.create_blip(0).play()
                    self.last_selected = self.selected
            
            if spinner.is_left_clicked():
                self.adjusting = True
                self.rotation_accumulator = 0.0
                self.synth.create_select().play()
            if spinner.is_right_clicked():
                self.config.save()
                self.synth.create_back().play()
                return "main_menu"
        else:
            if self.selected == 0:
                self.config.spinner_sensitivity += spinner_delta * 0.3
                self.config.spinner_sensitivity = max(10, min(200, self.config.spinner_sensitivity))
            elif self.selected == 1:
                self.rotation_accumulator += spinner_delta
                if abs(self.rotation_accumulator) >= 50.0 and self.adjustment_cooldown <= 0:
                    current_idx = self.resolutions.index(self.config.resolution)
                    direction = 1 if self.rotation_accumulator > 0 else -1
                    new_idx = (current_idx + direction) % len(self.resolutions)
                    self.config.resolution = self.resolutions[new_idx]
                    self.rotation_accumulator = 0.0
                    self.needs_display_update = True
                    self.synth.create_blip(direction).play()
            elif self.selected == 2:
                self.rotation_accumulator += spinner_delta
                if abs(self.rotation_accumulator) >= 50.0 and self.adjustment_cooldown <= 0:
                    self.config.fullscreen = not self.config.fullscreen
                    self.rotation_accumulator = 0.0
                    self.needs_display_update = True
                    self.synth.create_blip(0).play()
            
            if spinner.is_left_clicked():
                self.adjusting = False
                self.rotation_accumulator = 0.0
                self.config.save()
                self.synth.create_select().play()
        return None
    
    def draw(self, surface: pygame.Surface):
        # Disegna lo sfondo animato invece del colore solido
        self.background.draw(surface)
        
        title = self.font_title.render("SETTINGS", True, (255, 215, 0))
        surface.blit(title, (640 - title.get_width()//2, 80))
        
        options = [
            f"Sensitivity: {int(self.config.spinner_sensitivity)}%",
            f"Resolution: {self.config.resolution[0]}x{self.config.resolution[1]}",
            f"Fullscreen: {'ON' if self.config.fullscreen else 'OFF'}"
        ]
        
        y = 250
        for i, option in enumerate(options):
            is_selected, is_adjusting = i == self.selected, i == self.selected and self.adjusting
            color = (0, 255, 100) if is_adjusting else ((255, 255, 0) if is_selected else (180, 180, 180))
            font = self.font_item_selected if is_selected else self.font_item
            
            if is_adjusting:
                ind_txt = self.font_indicator.render("< ADJUSTING >", True, (0, 255, 100))
                surface.blit(ind_txt, (640 - ind_txt.get_width()//2, y - 35))
            
            text = font.render(option, True, color)
            surface.blit(text, (640 - text.get_width()//2, y))
            
            if i == 0 and is_selected:
                bar_x, bar_y, bar_width, bar_height = 440, y + 55, 400, 8
                pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
                fill_width = int((self.config.spinner_sensitivity / 200.0) * bar_width)
                fill_color = (0, 255, 100) if is_adjusting else (255, 255, 0)
                pygame.draw.rect(surface, fill_color, (bar_x, bar_y, fill_width, bar_height))
            y += 110
        
        y = 600
        hints = ["SPINNER: Navigate", "LEFT: Adjust | RIGHT: Back to Menu"] if not self.adjusting else ["SPINNER: Modify", "LEFT: Confirm"]
        for hint_text in hints:
            hint = self.font_hint.render(hint_text, True, (100, 200, 100))
            surface.blit(hint, (640 - hint.get_width()//2, y))
            y += 35

# ============== PLAYING STATE ==============
class PlayingState(GameState):
    def __init__(self, game: MiniGame, high_score_mgr: HighScoreManager, synth: SoundSynthesizer):
        self.game = game
        self.high_score_mgr = high_score_mgr
        self.synth = synth
    
    def on_enter(self):
        self.game.reset()
        self.synth.create_game_start().play()
    
    def update(self, dt: float, spinner_delta: float, spinner: SpinnerInput) -> Optional[str]:
        continue_playing = self.game.update(dt, spinner_delta, spinner)
        if not continue_playing or self.game.is_game_over():
            if self.game.is_game_over():
                score = self.game.get_score()
                if self.high_score_mgr.is_high_score(self.game.get_name(), score):
                    return f"name_entry:{self.game.get_name()}:{score}"
                else:
                    self.synth.create_game_over().play()
                    return f"view_scores:{self.game.get_name()}"
            self.synth.create_back().play()
            return "main_menu"
        return None
    
    def draw(self, surface: pygame.Surface):
        self.game.draw(surface)










class BreakoutSpinner(MiniGame):
    # Power-up types
    POWERUP_TYPES = {
        'multiball': {'color': (255, 200, 100), 'duration': 0},
        'bigpaddle': {'color': (100, 200, 255), 'duration': 8.0},
        'slowball': {'color': (150, 255, 150), 'duration': 6.0},
        'fireball': {'color': (255, 100, 50), 'duration': 10.0},
        'magnet': {'color': (255, 150, 255), 'duration': 8.0},
        'laser': {'color': (255, 255, 100), 'duration': 5.0},
        'extralife': {'color': (255, 50, 50), 'duration': 0},
        'scoreup': {'color': (255, 215, 0), 'duration': 10.0}
    }
    
    # === CACHE PER RENDERING ===
    _brick_cache = {}  # Cache per brick surfaces pre-renderizzati
    _powerup_cache = {}  # Cache per powerup shapes
    
    def __init__(self, synth: SoundSynthesizer):
        super().__init__()
        self.synth = synth
        
        # Core game state
        self.paddle_x = 640
        self.paddle_width = 120
        self.paddle_target_width = 120
        self.balls = []
        self.bricks = []
        self.particles = []
        self.powerups = []
        self.lasers = []
        self.floating_texts = []
        
        # Level system
        self.level = 1
        self.max_level = 20
        self.level_complete_timer = 0
        
        # Lives and score
        self.lives = 3
        self.max_lives = 5
        self.combo = 0
        self.combo_timer = 0
        self.combo_multiplier = 1.0
        self.max_combo = 0
        
        # Power-ups
        self.active_powerups = {}
        self.powerup_spawn_timer = 0
        
        # Visual effects
        self.screen_shake = 0
        self.flash_timer = 0
        self.time = 0
        self.paddle_pulse = 0
        self.background_wave = 0
        
        # Pause menu
        self.paused = False
        self.confirm_exit = False
        
        # Stats
        self.total_bricks_broken = 0
        self.powerups_collected = 0
        self.total_shots = 0
        
        # Fonts - ridotti per HUD minimale
        self.font_score = pygame.font.Font(None, 28)
        self.font_level = pygame.font.Font(None, 32)
        self.font_combo = pygame.font.Font(None, 26)
        self.font_pause = pygame.font.Font(None, 80)
        self.font_hint = pygame.font.Font(None, 24)
        self.font_powerup = pygame.font.Font(None, 20)
        
        # === CACHE SUPERFICI HUD ===
        self._hud_cache = {}
        self._last_score = -1
        self._last_level = -1
        self._last_combo = -1
        
        self.reset()
    
    def get_name(self) -> str:
        return "Breakout Spinner"
    
    def get_description(self) -> str:
        return "Epic breakout with 20 levels and powerups!"
    
    def reset(self):
        self.score = 0
        self.game_over = False
        self.level = 1
        self.lives = 3
        self.combo = 0
        self.combo_timer = 0
        self.combo_multiplier = 1.0
        self.max_combo = 0
        self.paused = False
        self.confirm_exit = False
        self.total_bricks_broken = 0
        self.powerups_collected = 0
        self.paddle_width = 120
        self.paddle_target_width = 120
        self.active_powerups = {}
        self.time = 0
        self.screen_shake = 0
        self.balls = []
        self.bricks = []
        self.particles = []
        self.powerups = []
        self.lasers = []
        self.floating_texts = []
        self._hud_cache.clear()
        self._last_score = -1
        self._last_level = -1
        self._last_combo = -1
        self.generate_level(self.level)
        self.spawn_ball()
    
    def spawn_ball(self):
        """Spawn a new ball from paddle"""
        angle = random.uniform(-60, -120)
        speed = 350 + self.level * 20
        self.balls.append({
            'x': self.paddle_x,
            'y': 650,
            'vx': math.cos(math.radians(angle)) * speed,
            'vy': math.sin(math.radians(angle)) * speed,
            'trail': [],
            'glow': 0
        })
    
    def generate_level(self, level: int):
        """Generate procedural brick patterns for each level"""
        self.bricks = []
        patterns = [
            self.pattern_standard,
            self.pattern_pyramid,
            self.pattern_walls,
            self.pattern_checkerboard,
            self.pattern_diamond,
            self.pattern_spiral,
            self.pattern_cross,
            self.pattern_circles,
            self.pattern_wave,
            self.pattern_maze
        ]
        
        # Use pattern based on level
        pattern_func = patterns[(level - 1) % len(patterns)]
        pattern_func(level)
        
        # Calculate brick strengths and colors based on level
        for brick in self.bricks:
            brick['strength'] = min(1 + (level - 1) // 3, 5)
            brick['max_strength'] = brick['strength']
            brick['alive'] = True
            brick['pulse'] = random.uniform(0, math.pi * 2)
            brick['hit_flash'] = 0
    
    def pattern_standard(self, level: int):
        """Standard grid pattern"""
        rows = 5 + min(level // 2, 5)
        for row in range(rows):
            for col in range(10):
                self.bricks.append({
                    'x': 40 + col * 120,
                    'y': 80 + row * 35,
                    'w': 110,
                    'h': 28
                })
    
    def pattern_pyramid(self, level: int):
        """Pyramid shape"""
        for row in range(8):
            width = 10 - row
            start_col = row // 2
            for col in range(width):
                self.bricks.append({
                    'x': 40 + (start_col + col) * 120,
                    'y': 80 + row * 35,
                    'w': 110,
                    'h': 28
                })
    
    def pattern_walls(self, level: int):
        """Side walls pattern"""
        for row in range(10):
            for col in [0, 1, 8, 9]:
                self.bricks.append({
                    'x': 40 + col * 120,
                    'y': 80 + row * 35,
                    'w': 110,
                    'h': 28
                })
    
    def pattern_checkerboard(self, level: int):
        """Checkerboard pattern"""
        for row in range(8):
            for col in range(10):
                if (row + col) % 2 == 0:
                    self.bricks.append({
                        'x': 40 + col * 120,
                        'y': 80 + row * 35,
                        'w': 110,
                        'h': 28
                    })
    
    def pattern_diamond(self, level: int):
        """Diamond shape"""
        center_row, center_col = 4, 5
        for row in range(9):
            for col in range(10):
                dist = abs(row - center_row) + abs(col - center_col)
                if dist <= 4:
                    self.bricks.append({
                        'x': 40 + col * 120,
                        'y': 80 + row * 35,
                        'w': 110,
                        'h': 28
                    })
    
    def pattern_spiral(self, level: int):
        """Spiral pattern"""
        positions = []
        x, y = 5, 4
        dx, dy = 0, -1
        for _ in range(50):
            if 0 <= x < 10 and 0 <= y < 8:
                positions.append((x, y))
            if x == y or (x < 0 and x == -y) or (x > 0 and x == 1-y):
                dx, dy = -dy, dx
            x, y = x+dx, y+dy
        
        for col, row in positions[:40]:
            self.bricks.append({
                'x': 40 + col * 120,
                'y': 80 + row * 35,
                'w': 110,
                'h': 28
            })
    
    def pattern_cross(self, level: int):
        """Cross shape"""
        for row in range(8):
            for col in range(10):
                if col == 4 or col == 5 or row == 3 or row == 4:
                    self.bricks.append({
                        'x': 40 + col * 120,
                        'y': 80 + row * 35,
                        'w': 110,
                        'h': 28
                    })
    
    def pattern_circles(self, level: int):
        """Circular pattern"""
        centers = [(2.5, 4), (7.5, 4)]
        for center_x, center_y in centers:
            for row in range(8):
                for col in range(10):
                    dist = math.sqrt((col - center_x)**2 + (row - center_y)**2)
                    if 1.5 <= dist <= 3:
                        self.bricks.append({
                            'x': 40 + col * 120,
                            'y': 80 + row * 35,
                            'w': 110,
                            'h': 28
                        })
    
    def pattern_wave(self, level: int):
        """Wave pattern"""
        for col in range(10):
            wave_height = int(4 + 3 * math.sin(col * 0.8))
            for row in range(wave_height):
                self.bricks.append({
                    'x': 40 + col * 120,
                    'y': 80 + row * 35,
                    'w': 110,
                    'h': 28
                })
    
    def pattern_maze(self, level: int):
        """Maze-like pattern"""
        maze = [
            [1,1,1,0,0,0,0,1,1,1],
            [1,0,1,0,1,1,0,1,0,1],
            [1,0,1,0,1,1,0,1,0,1],
            [1,0,0,0,0,0,0,0,0,1],
            [1,1,1,0,1,1,0,1,1,1],
            [0,0,1,0,1,1,0,1,0,0],
            [1,0,1,0,0,0,0,1,0,1],
            [1,1,1,1,1,1,1,1,1,1]
        ]
        for row in range(len(maze)):
            for col in range(len(maze[0])):
                if maze[row][col]:
                    self.bricks.append({
                        'x': 40 + col * 120,
                        'y': 80 + row * 35,
                        'w': 110,
                        'h': 28
                    })
    




    
    def spawn_powerup(self, x: float, y: float):
        """Spawn random powerup at position"""
        if random.random() < 0.1:  # 10% chance
            pu_type = random.choice(list(self.POWERUP_TYPES.keys()))
            self.powerups.append({
                'x': x,
                'y': y,
                'vy': 150,
                'type': pu_type,
                'pulse': 0,
                'rotation': 0
            })
    




    def activate_powerup(self, pu_type: str):
        """Activate collected powerup"""
        self.powerups_collected += 1
        duration = self.POWERUP_TYPES[pu_type]['duration']
        
        if pu_type == 'multiball':
            for _ in range(2):
                if self.balls:
                    ball = self.balls[0]
                    angle = random.uniform(0, 360)
                    speed = math.sqrt(ball['vx']**2 + ball['vy']**2)
                    self.balls.append({
                        'x': ball['x'],
                        'y': ball['y'],
                        'vx': math.cos(math.radians(angle)) * speed,
                        'vy': math.sin(math.radians(angle)) * speed,
                        'trail': [],
                        'glow': 0
                    })
            self.create_floating_text(self.paddle_x, 650, "+2 BALLS!", (255, 200, 100))
            self.synth.create_multiball().play()
        
        elif pu_type == 'bigpaddle':
            self.paddle_target_width = 180
            self.active_powerups['bigpaddle'] = duration
            self.create_floating_text(self.paddle_x, 650, "BIG PADDLE!", (100, 200, 255))
            self.synth.create_powerup().play()
        
        elif pu_type == 'slowball':
            self.active_powerups['slowball'] = duration
            self.create_floating_text(self.paddle_x, 650, "SLOW BALL!", (150, 255, 150))
            self.synth.create_powerup().play()
        
        elif pu_type == 'fireball':
            self.active_powerups['fireball'] = duration
            self.create_floating_text(self.paddle_x, 650, "FIREBALL!", (255, 100, 50))
            self.synth.create_powerup().play()
        
        elif pu_type == 'magnet':
            self.active_powerups['magnet'] = duration
            self.create_floating_text(self.paddle_x, 650, "MAGNET!", (255, 150, 255))
            self.synth.create_shield_activate().play()
        
        elif pu_type == 'laser':
            self.active_powerups['laser'] = duration
            self.create_floating_text(self.paddle_x, 650, "LASER!", (255, 255, 100))
            self.synth.create_powerup().play()
        
        elif pu_type == 'extralife':
            if self.lives < self.max_lives:
                self.lives += 1
                self.create_floating_text(self.paddle_x, 650, "+1 LIFE!", (255, 50, 50))
                self.synth.create_high_score().play()
        
        elif pu_type == 'scoreup':
            self.active_powerups['scoreup'] = duration
            self.create_floating_text(self.paddle_x, 650, "SCORE x2!", (255, 215, 0))
            self.synth.create_powerup().play()
    
    def create_particles(self, x: float, y: float, color: tuple, count: int = 15):
        """Create particle burst"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(80, 200)
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'lifetime': random.uniform(0.3, 0.7),
                'max_lifetime': 0.7,
                'color': color,
                'size': random.uniform(2, 5)
            })
    
    def create_floating_text(self, x: float, y: float, text: str, color: tuple):
        """Create floating score text"""
        self.floating_texts.append({
            'x': x,
            'y': y,
            'text': text,
            'color': color,
            'lifetime': 1.5,
            'vy': -80
        })
    
    def update(self, dt: float, spinner_delta: float, spinner: SpinnerInput) -> bool:
        if self.game_over:
            return not spinner.is_right_clicked()
        
        self.time += dt
        self.background_wave += dt
        
        # Pause menu - FIXED: Funziona come gli altri minigiochi
        if spinner.is_right_clicked() and not self.paused:
            self.paused = True
            self.confirm_exit = False
            return True
        
        if self.paused:
            if spinner.is_left_clicked():
                self.synth.create_back().play()
                self.game_over = True
                return False
            if spinner.is_right_clicked():
                self.paused = False
                self.synth.create_select().play()
            return True
        
        # Level complete check
        if self.level_complete_timer > 0:
            self.level_complete_timer -= dt
            if self.level_complete_timer <= 0:
                self.level_complete_timer = 0 
                self.level += 1
                if self.level > self.max_level:
                    self.game_over = True
                    return not spinner.is_right_clicked()
                self.generate_level(self.level)
                self.balls = []
                self.spawn_ball()
            return True
        
        # Paddle movement
        self.paddle_x += spinner_delta * 7
        self.paddle_x = max(self.paddle_width // 2, min(1280 - self.paddle_width // 2, self.paddle_x))
        
        # Smooth paddle width transition
        if self.paddle_width < self.paddle_target_width:
            self.paddle_width += dt * 120
            if self.paddle_width > self.paddle_target_width:
                self.paddle_width = self.paddle_target_width
        elif self.paddle_width > self.paddle_target_width:
            self.paddle_width -= dt * 120
            if self.paddle_width < self.paddle_target_width:
                self.paddle_width = self.paddle_target_width
        
        self.paddle_pulse += dt * 4
        
        # Update power-ups timers
        expired = []
        for pu_type, timer in self.active_powerups.items():
            self.active_powerups[pu_type] = timer - dt
            if self.active_powerups[pu_type] <= 0:
                expired.append(pu_type)
        
        for pu_type in expired:
            del self.active_powerups[pu_type]
            if pu_type == 'bigpaddle':
                self.paddle_target_width = 120
        
        # Ball speed modifier
        speed_mult = 0.7 if 'slowball' in self.active_powerups else 1.0
        
        # Update balls
        for ball in self.balls[:]:
            ball['glow'] += dt * 6
            
            # Trail effect
            ball['trail'].append((ball['x'], ball['y']))
            if len(ball['trail']) > 8:
                ball['trail'].pop(0)
            
            # Magnet effect
            if 'magnet' in self.active_powerups:
                dist_to_paddle = ball['x'] - self.paddle_x
                if 650 <= ball['y'] <= 680 and abs(dist_to_paddle) < 200:
                    pull_force = (self.paddle_x - ball['x']) * 3
                    ball['vx'] += pull_force * dt
            
            ball['x'] += ball['vx'] * dt * speed_mult
            ball['y'] += ball['vy'] * dt * speed_mult
            
            # Wall collisions
            if ball['x'] <= 10 or ball['x'] >= 1270:
                ball['vx'] *= -1
                ball['x'] = max(10, min(1270, ball['x']))
                self.synth.create_wall_bounce().play()
                self.create_particles(ball['x'], ball['y'], (150, 200, 255), 8)
            
            if ball['y'] <= 10:
                ball['vy'] *= -1
                ball['y'] = 10
                self.synth.create_wall_bounce().play()
                self.create_particles(ball['x'], ball['y'], (150, 200, 255), 8)
            
            # Paddle collision
            if (670 <= ball['y'] <= 690 and 
                self.paddle_x - self.paddle_width // 2 <= ball['x'] <= self.paddle_x + self.paddle_width // 2):
                ball['vy'] = abs(ball['vy']) * -1
                offset = (ball['x'] - self.paddle_x) / (self.paddle_width // 2)
                ball['vx'] = offset * 400
                self.synth.create_paddle_hit().play()
                self.create_particles(ball['x'], ball['y'], (255, 255, 100), 10)
                self.paddle_pulse = 0
            
            # Ball lost
            if ball['y'] > 720:
                self.balls.remove(ball)
                if not self.balls:
                    self.lives -= 1
                    self.combo = 0
                    self.combo_timer = 0
                    if self.lives <= 0:
                        self.game_over = True
                        self.synth.create_game_over().play()
                    else:
                        self.spawn_ball()
                        self.synth.create_ball_lost().play()
        
        # Brick collisions
        fireball_active = 'fireball' in self.active_powerups
        
        for ball in self.balls:
            for brick in self.bricks:
                if not brick['alive']:
                    continue
                
                if (brick['x'] <= ball['x'] <= brick['x'] + brick['w'] and
                    brick['y'] <= ball['y'] <= brick['y'] + brick['h']):
                    
                    # Hit brick
                    if fireball_active:
                        brick['strength'] = 0
                    else:
                        brick['strength'] -= 1
                    
                    brick['hit_flash'] = 0.2
                    
                    if brick['strength'] <= 0:
                        brick['alive'] = False
                        self.total_bricks_broken += 1
                        
                        # Score with combo
                        points = int(10 * self.combo_multiplier * (2 if 'scoreup' in self.active_powerups else 1))
                        self.score += points
                        
                        # Combo system
                        self.combo += 1
                        self.combo_timer = 2.0
                        self.max_combo = max(self.max_combo, self.combo)
                        self.combo_multiplier = 1.0 + (self.combo // 5) * 0.5
                        
                        # Effects - RIDOTTO SCREEN SHAKE
                        color = self.get_brick_color(brick)
                        self.create_particles(brick['x'] + brick['w'] // 2, brick['y'] + brick['h'] // 2, color, 20)
                        self.create_floating_text(brick['x'] + brick['w'] // 2, brick['y'], f"+{points}", (255, 255, 100))
                        self.screen_shake = 0.08
                        self.synth.create_score_point().play()
                        
                        self.spawn_powerup(brick['x'] + brick['w'] // 2, brick['y'] + brick['h'] // 2)
                    else:
                        self.synth.create_hit().play()
                        self.create_particles(ball['x'], ball['y'], (255, 150, 100), 8)
                        self.screen_shake = 0.04
                    
                    if not fireball_active:
                        ball['vy'] *= -1
                    break
        
        # Check level complete
        if all(not brick['alive'] for brick in self.bricks) and self.level_complete_timer == 0:
            self.level_complete_timer = 2.0
            self.score += 500 * self.level
            self.create_floating_text(640, 360, f"LEVEL {self.level} COMPLETE!", (255, 215, 0))
            self.synth.create_level_complete().play()
        
        # Update powerups falling
        for pu in self.powerups[:]:
            pu['y'] += pu['vy'] * dt
            pu['pulse'] += dt * 5
            pu['rotation'] += dt * 180
            
            # Collect powerup
            if (670 <= pu['y'] <= 690 and
                self.paddle_x - self.paddle_width // 2 <= pu['x'] <= self.paddle_x + self.paddle_width // 2):
                self.activate_powerup(pu['type'])
                self.powerups.remove(pu)
                continue
            
            if pu['y'] > 720:
                self.powerups.remove(pu)
        
        # Laser shooting
        if 'laser' in self.active_powerups and spinner.is_left_clicked():
            self.lasers.append({'x': self.paddle_x - 20, 'y': 670, 'vy': -800})
            self.lasers.append({'x': self.paddle_x + 20, 'y': 670, 'vy': -800})
            self.synth.create_laser_shoot().play()
        
        # Update lasers
        for laser in self.lasers[:]:
            laser['y'] += laser['vy'] * dt
            
            for brick in self.bricks:
                if (brick['alive'] and
                    brick['x'] <= laser['x'] <= brick['x'] + brick['w'] and
                    brick['y'] <= laser['y'] <= brick['y'] + brick['h']):
                    brick['strength'] -= 1
                    if brick['strength'] <= 0:
                        brick['alive'] = False
                        self.score += 10
                        self.total_bricks_broken += 1
                        color = self.get_brick_color(brick)
                        self.create_particles(brick['x'] + brick['w'] // 2, brick['y'] + brick['h'] // 2, color, 15)
                        self.synth.create_score_point().play()
                        self.spawn_powerup(brick['x'] + brick['w'] // 2, brick['y'] + brick['h'] // 2)
                    self.lasers.remove(laser)
                    break
            
            if laser['y'] < 0:
                self.lasers.remove(laser)
        
        # Update combo timer
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 0
                self.combo_multiplier = 1.0
        
        # Update particles
        for p in self.particles[:]:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] += 400 * dt
            p['lifetime'] -= dt
            if p['lifetime'] <= 0:
                self.particles.remove(p)
        
        # Update floating texts
        for ft in self.floating_texts[:]:
            ft['y'] += ft['vy'] * dt
            ft['lifetime'] -= dt
            if ft['lifetime'] <= 0:
                self.floating_texts.remove(ft)
        
        # Update brick animations
        for brick in self.bricks:
            brick['pulse'] += dt * 2
            if brick['hit_flash'] > 0:
                brick['hit_flash'] -= dt
        
        # Screen shake
        if self.screen_shake > 0:
            self.screen_shake -= dt
        
        return not spinner.is_right_clicked()
    
    def get_brick_color(self, brick: dict) -> tuple:
        """Get brick color based on strength"""
        strength_ratio = brick['strength'] / brick['max_strength']
        if strength_ratio > 0.75:
            return (200, 50, 50)
        elif strength_ratio > 0.5:
            return (200, 100, 50)
        elif strength_ratio > 0.25:
            return (200, 150, 50)
        else:
            return (200, 200, 50)
    
    def _get_cached_brick(self, color: tuple, w: int, h: int, pulse: float, flash: float) -> pygame.Surface:
        """Cached brick rendering"""
        cache_key = (color, w, h, int(pulse * 10), int(flash * 10))
        if cache_key not in self._brick_cache:
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            if flash > 0:
                flash_intensity = int(flash * 255)
                color = tuple(min(255, c + flash_intensity) for c in color)
            
            pygame.draw.rect(surf, color, (0, 0, w, h), 0, 5)
            lighter = tuple(min(255, c + 50) for c in color)
            pygame.draw.rect(surf, lighter, (0, 0, w, h), 2, 5)
            self._brick_cache[cache_key] = surf
            
            # Limit cache size
            if len(self._brick_cache) > 200:
                self._brick_cache.pop(next(iter(self._brick_cache)))
        
        return self._brick_cache[cache_key]
    
    def _get_cached_powerup(self, pu_type: str, rotation: float, pulse_size: float) -> pygame.Surface:
        """Cached powerup rendering"""
        cache_key = (pu_type, int(rotation) % 360, int(pulse_size))
        if cache_key not in self._powerup_cache:
            pu_color = self.POWERUP_TYPES[pu_type]['color']
            size = int(pulse_size * 3)
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            
            points = []
            for i in range(4):
                angle = math.radians(rotation + i * 90)
                px = size // 2 + math.cos(angle) * pulse_size
                py = size // 2 + math.sin(angle) * pulse_size
                points.append((px, py))
            
            pygame.draw.polygon(surf, pu_color, points)
            pygame.draw.polygon(surf, (255, 255, 255), points, 2)
            
            self._powerup_cache[cache_key] = surf
            
            # Limit cache
            if len(self._powerup_cache) > 50:
                self._powerup_cache.pop(next(iter(self._powerup_cache)))
        
        return self._powerup_cache[cache_key]
    
    def _get_background_colors(self, level: int) -> tuple:
        """Get background gradient colors based on level"""
        themes = [
            ((15, 15, 30), (25, 25, 45)),    # Level 1-2: Deep blue
            ((20, 10, 30), (35, 20, 50)),    # Level 3-4: Purple
            ((10, 20, 25), (20, 35, 45)),    # Level 5-6: Teal
            ((25, 15, 10), (40, 25, 20)),    # Level 7-8: Brown/red
            ((10, 25, 15), (20, 40, 30)),    # Level 9-10: Forest green
            ((30, 10, 15), (50, 20, 30)),    # Level 11-12: Crimson
            ((15, 10, 25), (30, 20, 45)),    # Level 13-14: Indigo
            ((25, 20, 10), (45, 35, 20)),    # Level 15-16: Gold/orange
            ((10, 15, 30), (20, 30, 55)),    # Level 17-18: Ocean blue
            ((20, 10, 20), (40, 20, 40)),    # Level 19-20: Magenta
        ]
        theme_idx = min((level - 1) // 2, len(themes) - 1)
        return themes[theme_idx]
    







    def draw(self, surface: pygame.Surface):
        """Metodo principale di disegno - Scomposto in moduli"""
        # Calcolo shake
        shake_x, shake_y = self._get_shake_offset()

        # 1. Sfondo e elementi livello
        self._draw_background_layers(surface)
        
        # 2. Elementi di gioco dinamici
        self._draw_bricks(surface, shake_x, shake_y)
        self._draw_powerups(surface, shake_x, shake_y)
        self._draw_lasers(surface, shake_x, shake_y)
        self._draw_paddle(surface, shake_x, shake_y)
        self._draw_balls(surface, shake_x, shake_y)
        self._draw_particles(surface, shake_x, shake_y)
        self._draw_floating_texts(surface)
        
        # 3. Interfaccia utente (HUD)
        self.draw_hud(surface)

        # 4. Overlay (Pause, Level Complete, Game Over)
        self._draw_overlays(surface)

    def _get_shake_offset(self):
        """Calcola l'offset per lo screen shake"""
        shake_x = shake_y = 0
        if self.screen_shake > 0:
            shake_x = random.randint(-3, 3)
            shake_y = random.randint(-3, 3)
        return shake_x, shake_y













    def _draw_background_layers(self, surface):
        """Ultra-optimized 6-level backgrounds: No white glare, 60+fps, error-free"""
        base_color, accent_color = self._get_background_colors(self.level)
        self.background_wave += 0.025

        star_cache = {}

        for y in range(0, 720, 2):
            factor = y / 720
            noise1 = 18 * math.sin(self.background_wave * 1.1 + factor * 1.4)
            noise2 = 12 * math.cos(self.background_wave * 0.9 + factor * 1.7)
            r = max(8, min(255, int(base_color[0] + noise1 + noise2 * 0.6)))
            g = max(8, min(255, int(base_color[1] + noise1 * 0.7 + noise2)))
            b = max(8, min(255, int(base_color[2] + noise1 * 0.5 + noise2 * 1.2)))
            pygame.draw.line(surface, (r, g, b), (0, y), (1280, y))
            pygame.draw.line(surface, (max(0,r-2), max(0,g-2), max(0,b-2)), (0, y+1), (1280, y+1))

        level_type = self.level % 6
        accent_dark = tuple(max(20, int(c * 0.75)) for c in accent_color)
        glow_dark = tuple(min(240, int(accent_color[j] * 1.3)) for j in range(3))

        if level_type == 0:
            for deep_layer in range(5):
                parallax = self.background_wave * (0.3 + deep_layer * 0.15)
                star_density = 42 - deep_layer * 7
                star_tint = tuple(min(240, int(accent_color[j] * (0.4 + deep_layer * 0.12))) for j in range(3))
                for star_id in range(star_density):
                    cache_key = (deep_layer, star_id % 16)
                    if cache_key not in star_cache:
                        twinkle = math.sin(self.background_wave * 4.2 + star_id * 0.47 + deep_layer)
                        brightness = int(110 + 95 * (twinkle * 0.55 + 0.45))
                        size = max(1, 2 + deep_layer // 3)
                        star_surf = pygame.Surface((size*5, size*5), pygame.SRCALPHA)
                        core_r = (brightness//3, brightness//4, min(235, brightness + 10))
                        halo_r = (brightness//5, brightness//6, min(215, brightness))
                        pygame.draw.circle(star_surf, core_r, (size*2+1, size*2+1), size*2)
                        pygame.draw.circle(star_surf, halo_r, (size*2+1, size*2+1), size*3)
                        star_cache[cache_key] = star_surf, star_tint
                    star_surf, tint = star_cache[cache_key]
                    star_x = (star_id * 23.7 + parallax * 95 + deep_layer * 47) % 1280
                    star_y = (star_id * 29.1 + parallax * 62 + deep_layer * 89) % 720
                    surface.blit(star_surf, (int(star_x-size*2), int(star_y-size*2)))
            for constel in range(6):
                cx = (constel * 213 + self.background_wave * 14) % 1280
                cy = 210 + constel * 98 + int(11 * math.sin(self.background_wave * 0.8 + constel))
                points = [(cx + int(32 * math.cos(a)), cy + int(32 * math.sin(a))) 
                        for a in [self.background_wave * 1.3 + i*1.047 for i in range(6)]]
                line_alpha = int(95 + 45 * math.sin(self.background_wave * 2.1 + constel))
                for i in range(6):
                    pygame.draw.line(surface, (*accent_dark, max(0,line_alpha//3)), points[i], points[(i+1)%6], 1)
        elif level_type == 1:
            for nebula_layer in range(5):
                expand = self.background_wave * 0.42 + nebula_layer * 0.73
                pulse = abs(math.sin(expand * 1.9)) * 0.42 + 0.58
                nx = 640 + int(200 * math.cos(expand * 0.34))
                ny = 360 + int(160 * math.sin(expand * 0.28))
                nr = 78 + int(38 * pulse) + nebula_layer * 16
                for ring_step in range(0, nr, 3):
                    ring_a = int((75 + nebula_layer * 20) * (1 - ring_step / nr)**1.3)
                    ring_c = tuple(int(accent_color[j] * (0.45 + nebula_layer * 0.11)) for j in range(3))
                    pygame.draw.circle(surface, (*ring_c, ring_a), (int(nx), int(ny)), ring_step, 1)
                for filament in range(10):
                    f_angle = (filament * 36 + expand * 2.4) % 360
                    f_len = 58 + int(22 * pulse)
                    fx1 = nx + int(nr * 0.65 * math.cos(math.radians(f_angle)))
                    fy1 = ny + int(nr * 0.65 * math.sin(math.radians(f_angle)))
                    fx2 = nx + int(f_len * math.cos(math.radians(f_angle)))
                    fy2 = ny + int(f_len * math.sin(math.radians(f_angle)))
                    f_thick = max(1, 2 - filament // 5)
                    f_glow = int(95 + 55 * pulse)
                    pygame.draw.line(surface, (*accent_dark, max(0,f_glow//3)), (fx1, fy1), (fx2, fy2), f_thick)
        elif level_type == 2:
            for swarm in range(6):
                speed = 0.28 + swarm * 0.19
                count = 52 - swarm * 6
                fade_rate = 42 + swarm * 8
                for pid in range(count):
                    flow = self.background_wave * speed + pid * 0.39
                    px = (pid * 21.4 + flow * 38) % 1280
                    py = (pid * 14.2 + flow * 27 + swarm * 73) % 720
                    trail_len = min(6, 5 + int(2.8 * abs(math.sin(flow * 2.1))))
                    for ts in range(trail_len):
                        tx = px + ts * 2.3 + int(1.2 * math.sin(flow + ts * 0.7))
                        ty = py + ts * 1.8 + int(1.1 * math.cos(flow * 1.4 + ts * 0.5))
                        ta = max(0, 255 - ts * fade_rate)
                        intensity = 0.9 + swarm * 0.08
                        tr = max(80, min(240, int(accent_color[0] * intensity + ta // 3.2)))
                        tg = max(90, min(240, int(accent_color[1] * intensity + ta // 3.8)))
                        tb = min(235, 220 + ta // 6)
                        size = max(1, 3 - ts // 2)
                        pygame.draw.circle(surface, (tr, tg, tb), (int(tx), int(ty)), size)
        elif level_type == 3:
            for row in range(13):
                ybase = row * 55 + int(10 * math.sin(self.background_wave * 1.4 + row))
                for col in range(21):
                    xbase = col * 61 + int(7 * math.cos(self.background_wave * 1.7 + col))
                    lx2 = xbase + 64
                    ly2 = ybase + int(5 * math.sin(self.background_wave * 1.5 + col + row))
                    weight = max(1, 2 + (row + col) // 14)
                    line_col = tuple(min(240, int(c * (1.1 + row * 0.04))) for c in glow_dark)
                    pygame.draw.line(surface, line_col, (xbase, ybase), (lx2, ly2), weight)
                    if (col + row * 3) % 5 == 0:
                        pulse = self.background_wave * 3.9 + row * 0.4 + col
                        nsize = 3 + int(1.8 * abs(math.sin(pulse)))
                        nbright = int(185 + 55 * math.sin(pulse * 1.6))
                        ncolor = tuple(min(235, nbright//2 + j*8) for j in range(3))
                        pygame.draw.circle(surface, ncolor, (int((xbase+lx2)/2), int((ybase+ly2)/2)), nsize)
        elif level_type == 4:
            for family in range(7):
                freq = 0.09 + family * 0.07
                amp = 32 + family * 8
                phase = family * 1.92 + self.background_wave * 1.45
                thick_base = max(2, 5 - family)
                for x1 in range(0, 1280, 10):
                    x2 = min(1280, x1 + 10)
                    oy1 = amp * math.sin((x1 + self.background_wave * 48) * freq + phase)
                    oy2 = amp * math.sin((x2 + self.background_wave * 48) * freq + phase)
                    wy1, wy2 = int(720 * 0.28 + 140 + oy1), int(720 * 0.28 + 140 + oy2)
                    cbase = tuple(min(240, int(accent_color[j] * (0.85 + family * 0.06))) for j in range(3))
                    bright = 1 + 0.15 * abs(math.sin(self.background_wave * 2.7 + family))
                    color = tuple(min(240, int(cb * bright)) for cb in cbase)
                    thick = thick_base + int(1.5 * abs(math.sin(phase + x1 * 0.03)))
                    pygame.draw.line(surface, color, (x1, wy1), (x2, wy2), thick)
        elif level_type == 5:
            for crystal in range(26):
                rot = self.background_wave * 1.62 + crystal * 0.37
                scale = 1 + 0.12 * abs(math.sin(self.background_wave * 2.9 + crystal))
                cx = (crystal * 49 + rot * 19) % 1280
                cy = (crystal * 27 + rot * 16 + 240) % 720
                points = []
                for f in range(12):
                    angle = math.radians((f * 30) + rot * 8.4)
                    rad = (24 + f * 1.8) * scale
                    points.append((cx + rad * math.cos(angle), cy + rad * math.sin(angle)))
                f_glow = tuple(min(240, int(accent_color[j] * (1.3 + abs(math.sin(rot)) * 0.22))) for j in range(3))
                e_glow = tuple(min(240, int(fg * 1.35)) for fg in f_glow)
                pygame.draw.polygon(surface, f_glow, points)
                pygame.draw.polygon(surface, e_glow, points, 2)

        if len(star_cache) > 32:
            star_cache.clear()














    def _draw_bricks(self, surface, shake_x, shake_y):
        """Disegna i mattoni usando la cache"""
        for brick in self.bricks:
            if not brick['alive']: continue
            color = self.get_brick_color(brick)
            pulse = abs(math.sin(brick['pulse'])) * 5
            brick_surf = self._get_cached_brick(color, brick['w'], brick['h'], 
                                              brick['pulse'], brick['hit_flash'])
            surface.blit(brick_surf, (brick['x'] + shake_x, brick['y'] + shake_y - pulse))
            
            if brick['max_strength'] > 1:
                for i in range(brick['strength']):
                    dot_x = brick['x'] + 10 + i * 8
                    dot_y = brick['y'] + brick['h'] // 2
                    pygame.draw.circle(surface, (255, 255, 255), 
                                     (int(dot_x) + shake_x, int(dot_y) + shake_y), 2)

    def _draw_powerups(self, surface, shake_x, shake_y):
        """Disegna i powerup cadenti"""
        for pu in self.powerups:
            pulse_size = 15 + abs(math.sin(pu['pulse'])) * 5
            pu_surf = self._get_cached_powerup(pu['type'], pu['rotation'], pulse_size)
            x_offset = pu['x'] - pu_surf.get_width() // 2 + shake_x
            y_offset = pu['y'] - pu_surf.get_height() // 2 + shake_y
            surface.blit(pu_surf, (x_offset, y_offset))

    def _draw_lasers(self, surface, shake_x, shake_y):
        """Disegna i laser"""
        for laser in self.lasers:
            pygame.draw.rect(surface, (255, 255, 100), 
                           (laser['x'] - 3 + shake_x, laser['y'] + shake_y, 6, 20))
            pygame.draw.rect(surface, (255, 255, 255), 
                           (laser['x'] - 2 + shake_x, laser['y'] + shake_y, 4, 20))











    def _draw_paddle(self, surface, shake_x, shake_y):
        """Disegna il paddle con effetti"""
        pulse_offset = abs(math.sin(self.paddle_pulse)) * 3
        paddle_rect = (self.paddle_x - self.paddle_width // 2 + shake_x, 
                      670 - pulse_offset + shake_y, 
                      self.paddle_width, 20)
        
        paddle_color = (255, 255, 255)
        if 'bigpaddle' in self.active_powerups:
            paddle_color = (100, 200, 255)
        elif 'laser' in self.active_powerups:
            paddle_color = (255, 255, 100)
        
        pygame.draw.rect(surface, paddle_color, paddle_rect, 0, 10)
        pygame.draw.rect(surface, (255, 255, 255), paddle_rect, 3, 10)
        
        if 'magnet' in self.active_powerups:
            for i in range(3):
                arc_rect = (self.paddle_x - 80 + shake_x, 670 - 60 + shake_y, 160, 60)
                pygame.draw.arc(surface, (255, 150, 255), arc_rect, 0, math.pi, 2)


    def _draw_balls(self, surface, shake_x, shake_y):
        """Disegna le palline con trail"""
        for ball in self.balls:
            # Trail
            for i, (tx, ty) in enumerate(ball['trail']):
                alpha = int(255 * (i / len(ball['trail'])))
                trail_color = (255, 255, 100) if 'fireball' not in self.active_powerups else (255, 100, 50)
                trail_surf = pygame.Surface((12, 12), pygame.SRCALPHA)
                pygame.draw.circle(trail_surf, (*trail_color, alpha // 2), (6, 6), 6)
                surface.blit(trail_surf, (tx - 6 + shake_x, ty - 6 + shake_y))
            
            # Glow
            glow_color = (255, 255, 150) if 'fireball' not in self.active_powerups else (255, 150, 50)
            glow_size = 20 + abs(math.sin(ball['glow'])) * 5
            glow_surf = pygame.Surface((int(glow_size * 2), int(glow_size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*glow_color, 40), 
                             (int(glow_size), int(glow_size)), int(glow_size))
            surface.blit(glow_surf, (ball['x'] - glow_size + shake_x, ball['y'] - glow_size + shake_y))
            
            # Ball core
            ball_color = (255, 255, 100) if 'fireball' not in self.active_powerups else (255, 100, 50)
            pygame.draw.circle(surface, ball_color, 
                             (int(ball['x']) + shake_x, int(ball['y']) + shake_y), 8)
            pygame.draw.circle(surface, (255, 255, 255), 
                             (int(ball['x']) + shake_x, int(ball['y']) + shake_y), 8, 2)











    def _draw_particles(self, surface, shake_x, shake_y):
        """Disegna particelle"""
        for p in self.particles:
            alpha = int(255 * (p['lifetime'] / p['max_lifetime']))
            p_surf = pygame.Surface((int(p['size'] * 2), int(p['size'] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (*p['color'], alpha), 
                             (int(p['size']), int(p['size'])), int(p['size']))
            surface.blit(p_surf, (p['x'] - p['size'] + shake_x, p['y'] - p['size'] + shake_y))

    def _draw_floating_texts(self, surface):
        """Disegna testi fluttuanti"""
        for ft in self.floating_texts:
            alpha = int(255 * (ft['lifetime'] / 1.5))
            text_surf = self.font_combo.render(ft['text'], True, ft['color'])
            text_surf.set_alpha(alpha)
            surface.blit(text_surf, (ft['x'] - text_surf.get_width() // 2, ft['y']))

    def _draw_overlays(self, surface):
        """Disegna schermate di overlay"""
        # Pause
        if self.paused:
            self.draw_pause_menu(surface)
            
        # Level Complete
        if self.level_complete_timer > 0:
            overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            surface.blit(overlay, (0, 0))
            
            complete_text = self.font_pause.render(f"LEVEL {self.level} COMPLETE!", True, (255, 215, 0))
            surface.blit(complete_text, (640 - complete_text.get_width() // 2, 300))
        
        # Game Over
        if self.game_over and self.level > self.max_level:
            overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))
            
            win_text = self.font_pause.render("YOU WIN!", True, (255, 215, 0))
            surface.blit(win_text, (640 - win_text.get_width() // 2, 250))
            
            final_score = self.font_level.render(f"Final Score: {self.score}", True, (255, 255, 255))
            surface.blit(final_score, (640 - final_score.get_width() // 2, 350))




























    def draw_hud(self, surface: pygame.Surface):
        """HUD 90s definitivo: visibile, trasparente, centrato, NO bug, completo."""
        
        # Barra trasparente elegante (visibile sempre)
        hud_rect = pygame.Rect(0, 0, 1280, 42)
        hud_surf = pygame.Surface(hud_rect.size, pygame.SRCALPHA)
        
        # Sfumatura trasparente (alpha basso)
        for y in range(42):
            alpha = 40 + int(30 * (1 - y / 42.0))
            col = (20, 20, 35, alpha)
            pygame.draw.line(hud_surf, col, (0, y), (1280, y))
        pygame.draw.line(hud_surf, (60, 60, 80, 140), (0, 41), (1280, 41), 2)
        surface.blit(hud_surf, hud_rect.topleft)
        
        center_y = 20  # Centro verticale
        font_main = self.font_level  # 32px
        
        # === SCORE sinistra ===
        score_str = f"SCORE {self.score:,}"
        score_text = font_main.render(score_str, True, (245, 245, 255))
        score_glow = font_main.render(score_str, True, (140, 160, 220))
        score_glow.set_alpha(120)
        surface.blit(score_glow, (32, center_y - score_text.get_height()//2 + 1))
        surface.blit(score_text, (30, center_y - score_text.get_height()//2))
        
        # === LEVEL centro ===
        level_str = f"L {self.level}/{self.max_level}"
        level_text = font_main.render(level_str, True, (255, 235, 140))
        level_glow = font_main.render(level_str, True, (210, 180, 90))
        level_glow.set_alpha(110)
        tx = 640 - level_text.get_width() // 2
        surface.blit(level_glow, (tx + 2, center_y - level_text.get_height()//2 + 1))
        surface.blit(level_text, (tx, center_y - level_text.get_height()//2))
        
        # === LIVES cuori perfetti (spazio 26px) ===
        for i in range(self.lives):
            heart_x = 1220 - i * 26
            self.draw_arcade_heart(surface, heart_x, center_y - 1, (255, 70, 70), 11)
        
        # === COMBO visibile SEMPRE se >0 (spazio dedicato 1150 centro) ===
        if self.combo > 0:
            combo_str = f"{self.combo}x"
            combo_text = self.font_combo.render(combo_str, True, (255, 255, 160))
            combo_glow = self.font_combo.render(combo_str, True, (180, 220, 255))
            combo_glow.set_alpha(130)
            cx = 1150 - combo_text.get_width() // 2
            surface.blit(combo_glow, (cx + 1, center_y - combo_text.get_height()//2 + 1))
            surface.blit(combo_text, (cx, center_y - combo_text.get_height()//2))
            
            # Timer barra orizzontale sotto (visibile)
            ratio = max(0, self.combo_timer / 2.0)
            bar_x = cx - 8
            bar_w = combo_text.get_width() + 16
            pygame.draw.rect(surface, (50, 50, 70, 160), (bar_x, center_y + 12, bar_w, 3))
            fill_w = int(bar_w * ratio)
            bar_col = (255, 255, 100) if ratio > 0.5 else (255, 200, 80)
            pygame.draw.rect(surface, (*bar_col, 220), (bar_x, center_y + 12, fill_w, 3))
            pygame.draw.rect(surface, (255, 255, 255, 180), (bar_x, center_y + 12, bar_w, 3), 1)
        
        # === ACTIVE POWERUPS: Dots glow dx ===
        pu_x = 1262
        pu_base_y = center_y - 12
        for idx, pu_type in enumerate(list(self.active_powerups.keys())[:4]):
            pu_info = self.POWERUP_TYPES[pu_type]
            pu_y = pu_base_y + idx * 14
            # Glow + dot
            pygame.draw.circle(surface, (*pu_info['color'], 80), (pu_x, pu_y), 8)
            pygame.draw.circle(surface, (*pu_info['color'], 200), (pu_x, pu_y), 5)

    def draw_arcade_heart(self, surface, x, y, color, size):
        """Cuore classico arcade: visibile perfetto."""
        # Proporzioni esatte breakout-style
        half = size // 2
        points = [
            (x, y + half // 2),
            (x - half + 1, y - half + 3),
            (x - half // 2, y - half),
            (x + 1, y - half // 2),
            (x + half // 2, y - half),
            (x + half - 1, y - half + 3)
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, (255, 255, 255), points, 1)


    def draw_pause_menu(self, surface: pygame.Surface):
        """Draw pause overlay"""
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        pause_text = self.font_pause.render("PAUSED", True, (255, 255, 255))
        surface.blit(pause_text, (640 - pause_text.get_width() // 2, 150))
        
        # Stats panel
        stats = [
            f"Score: {self.score}",
            f"Level: {self.level}/{self.max_level}",
            f"Max Combo: {self.max_combo}",
            f"Bricks: {self.total_bricks_broken}",
            f"Powerups: {self.powerups_collected}"
        ]
        
        y = 280
        for stat in stats:
            stat_text = self.font_combo.render(stat, True, (255, 255, 255))
            surface.blit(stat_text, (640 - stat_text.get_width() // 2, y))
            y += 40
        
        # Buttons
        exit_text = self.font_level.render("LEFT CLICK - Exit", True, (255, 100, 100))
        continue_text = self.font_level.render("RIGHT CLICK - Continue", True, (100, 255, 100))
        
        surface.blit(exit_text, (640 - exit_text.get_width() // 2, 550))
        surface.blit(continue_text, (640 - continue_text.get_width() // 2, 600))











class Kaleidoscope(MiniGame):
    """KALEIDOSCOPIO FULLSCREEN NO BORDI 60FPS"""

    BLEND_ADD = 1
    BLEND_MULT = 4
    
    def __init__(self, synth: SoundSynthesizer):
        super().__init__()
        self.synth = synth
        
        # CORE STATE
        self.time = 0.0
        self.global_hue = 0.0
        self.zoom_pulse = 1.0
        self.rotation_master = 0.0
        self.frame_counter = 0
        
        # FULLSCREEN DIMENSIONS
        self.cx, self.cy = 640, 360
        self.screen_w, self.screen_h = 1280, 720
        self.paused = False
        
        # PADDED BUFFERS 768x768 (pad=128px no edges)
        self.pad = 128
        buf_size = 512 + 2 * self.pad
        self.buffer_1 = pygame.Surface((buf_size, buf_size), pygame.SRCALPHA)
        self.buffer_1.convert_alpha()
        self.buffer_2 = pygame.Surface((buf_size, buf_size), pygame.SRCALPHA)
        self.buffer_2.convert_alpha()
        
        self.buf_cx = buf_size // 2
        self.buf_cy = buf_size // 2
        
        # FONTS
        self.font_pause = pygame.font.Font(None, 80)
        self.font_stats = pygame.font.Font(None, 28)

        self._init_all_systems()

    def _init_all_systems(self):
        self._init_particles()
        self._init_liquid()

    def _init_particles(self):
        self.num_particles = 200
        self.particles = []
        for i in range(self.num_particles):
            self.particles.append({
                'x': random.uniform(-1.5, 1.5),
                'y': random.uniform(-1.5, 1.5),
                'vx': random.uniform(-0.015, 0.015),
                'vy': random.uniform(-0.015, 0.015),
                'life': random.uniform(0, 1),
                'hue': random.uniform(0, 360),
                'size': random.uniform(2.0, 5.0),
                'sat': random.uniform(0.85, 1.0),
            })

    def update_particles(self, dt: float, spinner_factor: float):
        for p in self.particles:
            dx, dy = p['x'], p['y']
            r = math.hypot(dx, dy) or 0.001
            p['vx'] += -dx * 0.08 / (r**1.5) * dt
            p['vy'] += -dy * 0.08 / (r**1.5) * dt
            
            angle = math.atan2(dy, dx)
            p['vx'] += math.sin(angle + math.pi/2) * spinner_factor * 0.25 * dt
            p['vy'] -= math.cos(angle + math.pi/2) * spinner_factor * 0.25 * dt
            
            p['x'] += p['vx'] * dt * 60
            p['y'] += p['vy'] * dt * 60
            p['vx'] *= 0.97
            p['vy'] *= 0.97
            
            p['life'] = min(1.0, p['life'] + dt * 1.2)
            if p['life'] > 0.98 or r > 1.5:
                p['x'] = p['y'] = 0
                p['vx'] = random.uniform(-0.02, 0.02)
                p['vy'] = random.uniform(-0.02, 0.02)
                p['life'] = 0
                p['hue'] += random.uniform(-60, 60)

    def _init_liquid(self):
        self.liquid_size = 32
        self.liquid = [[0.0]*self.liquid_size for _ in range(self.liquid_size)]
        self.liquid_frame_skip = 0

    def update_liquid(self, dt: float):
        self.liquid_frame_skip += 1
        if self.liquid_frame_skip < 4: return
        self.liquid_frame_skip = 0
        
        new_grid = [[0.0]*self.liquid_size for _ in range(self.liquid_size)]
        for y in range(self.liquid_size):
            for x in range(self.liquid_size):
                sum_n = 0
                count = 0
                for dy in [-1,1]:
                    for dx in [-1,1]:
                        nx = (x + dx) % self.liquid_size
                        ny = (y + dy) % self.liquid_size
                        sum_n += self.liquid[ny][nx]
                        count += 1
                new_grid[y][x] = sum_n / count * 0.95
        self.liquid = new_grid

    def render_liquid(self, surf: pygame.Surface, cx: int, cy: int):
        surf.fill((0, 0, 0, 0))
        cell = 512 / self.liquid_size
        for y in range(self.liquid_size):
            for x in range(self.liquid_size):
                disp = self.liquid[y][x] * 50
                px = x * cell + cx + disp
                py = y * cell + cy + disp
                hue = (self.global_hue + x*2 + y*3) % 360
                color = self._hsv2rgb(hue, 0.95, 0.8)
                size = int(cell * 0.5)
                pygame.draw.circle(surf, (*color, 180), (int(px), int(py)), size)

    def render_particle_layer(self, surf: pygame.Surface, cx: int, cy: int):
        surf.fill((0,0,0,0))
        scale = 260
        for p in self.particles:
            l = p['life']
            s = int(p['size'] * (1 + l * 4))
            px, py = int(cx + p['x']*scale), int(cy + p['y']*scale)
            
            ch = (p['hue'] + l * 80) % 360
            cc = self._hsv2rgb(ch, p['sat'], 0.75 * l + 0.5)
            pygame.draw.circle(surf, (*cc, int(220 * l)), (px, py), s)

    def render_mandala_simple(self, surf: pygame.Surface, cx: int, cy: int):
        surf.fill((0, 0, 0, 0))
        for r in range(8):
            rad = 50 + r * 30
            thick = max(1, 18 - r)
            hue = (self.global_hue + r * 22 + self.rotation_master * 5) % 360
            
            for s in range(10):
                a = s * math.tau / 10 + self.rotation_master * 0.7 + r * 0.15
                x = cx + math.cos(a) * rad
                y = cy + math.sin(a) * rad
                color = self._hsv2rgb(hue, 0.95, 0.7)
                pygame.draw.circle(surf, (*color, 190), (int(x), int(y)), thick//2, 2)

    def _hsv2rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        v = min(0.8, v)
        if s < 0.7: s = 0.9
        h %= 360
        i = int(h // 60)
        f = (h / 60) - i
        p = v * (1 - s)
        q = v * (1 - s * f)
        t = v * (1 - s * (1 - f))
        idx = [ (v,t,p), (q,v,p), (p,v,t), (p,q,v), (t,p,v), (v,p,q) ]
        return tuple(int(c*255) for c in idx[i])

    def get_name(self) -> str: return "Kaleidoscope"
    def get_description(self) -> str: return "Fullscreen vivid seamless"

    def reset(self):
        self.time = self.global_hue = self.rotation_master = 0.0
        self.paused = False
        self._init_all_systems()

    def update(self, dt: float, spinner_delta: float, spinner: SpinnerInput) -> bool:
        if self.paused:
            return spinner.is_left_clicked() and (self.synth.create_back().play() or False)
        
        if spinner.is_right_clicked():
            self.paused = not self.paused
            if not self.paused: self.synth.create_select().play()
            return True

        if abs(spinner_delta) < 0.01: return True
        
        self.time += dt
        self.global_hue += dt * 28 * abs(spinner_delta)
        self.rotation_master += spinner_delta * dt * 120
        self.zoom_pulse = 0.92 + 0.16 * (math.sin(self.time * 3.5) ** 2)
        
        self.update_particles(dt, spinner_delta)
        self.update_liquid(dt)
        
        return True

    def _draw_pause_overlay(self, surface):
        ov = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        ov.fill((0,0,0,220))
        surface.blit(ov, (0,0))
        
        t = self.font_pause.render("PAUSED", True, (200,255,200))
        surface.blit(t, (self.cx-t.get_width()//2, 160))
        
        for i, txt in enumerate([f"L/R Click: Resume/Exit", f"T:{int(self.time)}s", f"P:{self.num_particles}"]):
            t = self.font_stats.render(txt, True, (150,220,150))
            surface.blit(t, (self.cx-t.get_width()//2, 450+i*32))

    def draw(self, surface: pygame.Surface):
        self.frame_counter += 1
        
        # GRADIENT FULLSCREEN
        gradient_surf = pygame.Surface((self.screen_w, self.screen_h))
        for i in range(0, self.screen_h, 16):
            h = (self.global_hue*0.3 + i*0.15) % 360
            c = self._hsv2rgb(h, 0.7, i/self.screen_h*0.25)
            pygame.draw.rect(gradient_surf, c, (0, i, self.screen_w, 16))
        surface.blit(gradient_surf, (0, 0))
        
        if self.paused:
            self._draw_pause_overlay(surface)
            return
        
        # RENDER WITH PADDED CENTER
        self.render_liquid(self.buffer_1, self.buf_cx, self.buf_cy)
        self.render_particle_layer(self.buffer_2, self.buf_cx, self.buf_cy)
        self.buffer_1.blit(self.buffer_2, (0,0), special_flags=self.BLEND_ADD)
        
        if self.frame_counter % 4 == 0:
            self.render_mandala_simple(self.buffer_2, self.buf_cx, self.buf_cy)
            self.buffer_1.blit(self.buffer_2, (0,0), special_flags=self.BLEND_ADD)
        
        effect = self._mirrors_fast(self.buffer_1)
        
        # FULL OVERLAP BLOOM (pad hides edges)
        scales = [1.3, 1.6]  # Slightly larger for coverage
        alphas = [200, 140]
        for scale, alpha in zip(scales, alphas):
            b = pygame.transform.smoothscale(effect, (int(1200*scale), int(1200*scale)))
            b.set_alpha(alpha)
            bx = self.cx - b.get_width()//2
            by = self.cy - b.get_height()//2
            surface.blit(b, (int(bx), int(by)), special_flags=self.BLEND_ADD)


    def _mirrors_fast(self, inp: pygame.Surface) -> pygame.Surface:
        out = self.buffer_2
        out.fill((0, 0, 0, 0))
        
        # 1. Pre-calcoliamo i valori costanti fuori dal ciclo
        rot = self.rotation_master * 0.35
        # L'angolo base che prima applicavi a r_surf
        base_angle = -rot * 10  
        
        num_wedges = 6
        # Convertiamo il passo del cuneo in gradi (math.tau radianti = 360 gradi)
        wedge_step_deg = 360.0 / num_wedges
        rot_deg = math.degrees(rot)
        
        # Cache dei riferimenti ai metodi (velocizza il loop a 60fps)
        rotate_func = pygame.transform.rotate
        blit_func = out.blit
        blend_mode = self.BLEND_ADD
        cx, cy = self.buf_cx, self.buf_cy

        for wedge in range(num_wedges):
            # 2. Unifichiamo le rotazioni in un'unica operazione
            # Angolo totale = (angolo del cuneo + rotazione master) + rotazione base
            total_angle = (wedge * wedge_step_deg) + rot_deg + base_angle
            
            # Una sola rotazione invece di due: meno perdita di qualità e molta più velocità
            w_surf = rotate_func(inp, total_angle)
            
            # 3. Posizionamento veloce al centro
            wr = w_surf.get_rect()
            wr.center = (cx, cy)
            
            blit_func(w_surf, wr.topleft, special_flags=blend_mode)
        
        # Nota: smoothscale è comunque lento, ma necessario per il risultato finale
        return pygame.transform.smoothscale(out, (1200, 1200))




























class YahtzeeSpinner(MiniGame):
    CATEGORIES = [
        ('ones', 'Ones', True),
        ('twos', 'Twos', True),
        ('threes', 'Threes', True),
        ('fours', 'Fours', True),
        ('fives', 'Fives', True),
        ('sixes', 'Sixes', True),
        ('three_kind', '3 of Kind', False),
        ('four_kind', '4 of Kind', False),
        ('full_house', 'Full House', False),
        ('sm_straight', 'Sm Straight', False),
        ('lg_straight', 'Lg Straight', False),
        ('yahtzee', 'YAHTZEE', False),
        ('chance', 'Chance', False)
    ]
    
    def __init__(self, synth=None):
        super().__init__()
        self.synth = synth
        self.spinner_buffer = 0 
        # Game state
        self.dice = [1, 1, 1, 1, 1]
        self.dice_held = [False] * 5
        self.selected_die = 0
        self.rolls_left = 3
        self.turn = 0
        
        # Click system
        self.left_hold_timer = 0.0
        self.left_hold_threshold = 0.5
        self.click_registered = False
        
        # Spinner control - SENSIBILITÀ DIVERSE PER FASE
        self.spinner_accumulator = 9000000000
        self.spinner_roll_threshold = 10  # AUMENTATO: serve più rotazione per lanciare
        self.spinner_select_threshold = 1.2 # ABBASSATO: rotazione minima per cambiare selezione
        self.can_roll = True
        self.roll_cooldown = 0
        
        # Scoring
        self.scores = {}
        self.upper_total = 0
        self.upper_bonus = 0
        self.lower_total = 0
        self.selected_category = 0
        
        # State machine
        self.phase = 'roll'
        self.paused = False
        self.roll_animation = 0
        
        # Visual
        self.particles = []
        self.floating_texts = []
        self.screen_shake = 0
        self.time = 0
        self.bg_wave = 0
        
        # Fonts
        self.font_huge = pygame.font.Font(None, 68)
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 26)
        self.font_tiny = pygame.font.Font(None, 19)
        self.font_pause = pygame.font.Font(None, 80)
        
        self.reset()
    
    def get_name(self) -> str:
        return "Yahtzee Spinner"
    
    def get_description(self) -> str:
        return "Spin to roll! Click to hold! Hold to confirm!"
    
    def reset(self):
        self.score = 0
        self.game_over = False
        self.dice = [random.randint(1, 6) for _ in range(5)]
        self.dice_held = [False] * 5
        self.selected_die = 0
        self.rolls_left = 3
        self.turn = 0
        self.left_hold_timer = 0.0
        self.click_registered = False
        self.spinner_accumulator = 0
        self.can_roll = True
        self.roll_cooldown = 0
        self.scores = {}
        self.upper_total = 0
        self.upper_bonus = 0
        self.lower_total = 0
        self.selected_category = 0
        self.phase = 'roll'
        self.paused = False
        self.roll_animation = 0
        self.particles = []
        self.floating_texts = []
        self.screen_shake = 0
        self.time = 0
        self.bg_wave = 0
        








            
    def roll_dice(self):
        """Lancia dadi non held - HIGH ENTROPY + FEEDBACK VISIVO"""
        if not self.can_roll or self.roll_animation > 0:
            return
        
        # 🔧 MAX ENTROPIA: seme unico per ogni roll
        import time
        import os
        random.seed(time.time_ns() ^ os.urandom(2).__hash__() ^ self.turn)
        
        rolled_any = False
        free_dice_indices = []
        
        print(f"🔄 Roll {4-self.rolls_left+1}/3 - Held: {self.dice_held}")
        
        for i in range(5):
            if not self.dice_held[i]:
                old_value = self.dice[i]
                
                # 🔥 HIGH ENTROPY: rigetta se uguale (95% cambia subito)
                new_value = old_value
                attempts = 0
                while new_value == old_value and attempts < 8:
                    new_value = random.randint(1, 6)
                    attempts += 1
                
                # Forza cambio se ancora uguale (raro)
                if new_value == old_value:
                    new_value = (old_value % 6) + 1
                
                self.dice[i] = new_value
                free_dice_indices.append(i)
                rolled_any = True
                print(f"  Dado {i}: {old_value}→{new_value} (attempts:{attempts})")
        
        if not rolled_any:
            print("⚠️ Nessun dado libero")
            return
        
        print(f"✅ Risultato: {[self.dice[j] for j in free_dice_indices]}")
        
        # Salva per flash visivo
        self.changed_dice = free_dice_indices
        self.flash_timer = 1.0
        
        # Stato aggiornato
        self.rolls_left -= 1
        self.roll_animation = 0.3  # Più veloce
        self.can_roll = False
        self.roll_cooldown = 0.5
        self.spinner_accumulator = 0
        
        # Effetti proporzionali
        particles = 20 + len(free_dice_indices) * 15
        self.create_particles(640, 420, (255, 255, 100), particles)
        self.screen_shake = min(0.2 + len(free_dice_indices)*0.08, 0.4)
        
        if self.synth:
            self.synth.create_score_point().play()
        
        # Prossima fase
        if self.rolls_left == 0:
            print("🎯 → SCORING")
            self.phase = 'scoring'
            self.selected_category = 0
        else:
            print("🔄 → SELECTING")
            self.phase = 'selecting'
            self.selected_die = 0














    def new_turn(self):
        """Inizia nuovo turno dopo aver scelto categoria"""
        self.rolls_left = 3
        self.dice_held = [False] * 5  # Tutti liberi
        self.phase = 'roll'
        self.can_roll = True
        self.roll_animation = 0
        self.roll_cooldown = 0
        self.selected_die = 0

    def calculate_score(self, cat_id: str, dice: List[int]) -> int:
        counts = [0] * 7
        for d in dice:
            counts[d] += 1
        
        if cat_id == 'ones': return counts[1] * 1
        if cat_id == 'twos': return counts[2] * 2
        if cat_id == 'threes': return counts[3] * 3
        if cat_id == 'fours': return counts[4] * 4
        if cat_id == 'fives': return counts[5] * 5
        if cat_id == 'sixes': return counts[6] * 6
        
        total = sum(dice)
        
        if cat_id == 'three_kind':
            return total if max(counts) >= 3 else 0
        if cat_id == 'four_kind':
            return total if max(counts) >= 4 else 0
        if cat_id == 'full_house':
            return 25 if (3 in counts and 2 in counts) else 0
        if cat_id == 'sm_straight':
            s = sorted(set(dice))
            for i in range(len(s) - 3):
                if s[i:i+4] == list(range(s[i], s[i] + 4)):
                    return 30
            return 0
        if cat_id == 'lg_straight':
            s = sorted(dice)
            if s == [1,2,3,4,5] or s == [2,3,4,5,6]:
                return 40
            return 0
        if cat_id == 'yahtzee':
            return 50 if max(counts) == 5 else 0
        if cat_id == 'chance':
            return total
        
        return 0
    

        
    def score_category(self, cat_id: str):
        if cat_id in self.scores:
            return
        self.turn += 1  # ← AGGIUNTO: questo era il problema principale!

        points = self.calculate_score(cat_id, self.dice)
        self.scores[cat_id] = points
        
        # Incrementa il turno DOPO aver registrato il punteggio
        
        is_upper = [c for c in self.CATEGORIES if c[0] == cat_id][0][2]
        if is_upper:
            self.upper_total += points
            if self.upper_total >= 63 and self.upper_bonus == 0:
                self.upper_bonus = 35
                self.create_floating_text(640, 300, "BONUS +35!", (255, 215, 0))
                if self.synth:
                    self.synth.create_high_score().play()
        else:
            self.lower_total += points
            if cat_id == 'yahtzee' and points == 50:
                self.create_floating_text(640, 360, "YAHTZEE!!!", (255, 50, 50))
                self.screen_shake = 0.6
                if self.synth:
                    self.synth.create_level_complete().play()
        
        self.score = self.upper_total + self.upper_bonus + self.lower_total
        
        if self.synth:
            self.synth.create_powerup().play()
        
        # Controlla se partita finita (ora turn parte da 0 e arriva a 13 dopo ultima categoria)
        if self.turn >= 13:  # ← Corretto: 13 categorie = turn 13 dopo ultima
            self.game_over = True
            self.create_floating_text(640, 400, "GAME COMPLETE!", (255, 215, 0))
            if self.synth:
                self.synth.create_game_over().play()
        else:
            # Reset per nuovo turno
            self.rolls_left = 3
            self.dice_held = [False] * 5
            self.phase = 'roll'
            self.can_roll = True
            self.roll_animation = 0
            self.roll_cooldown = 0
            self.selected_die = 0
            self.new_turn()  # ← OPZIONALE: se hai questa funzione, chiamala qui

    
    def create_particles(self, x: float, y: float, color: tuple, count: int):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(120, 300)
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(0.5, 1.2),
                'max_life': 1.2,
                'color': color,
                'size': random.uniform(3, 8)
            })
    
    def create_floating_text(self, x: float, y: float, text: str, color: tuple):
        self.floating_texts.append({
            'x': x, 'y': y, 'text': text, 'color': color,
            'life': 2.5, 'vy': -50
        })
    










    def update(self, dt: float, spinner_delta: float, spinner) -> bool:
        if self.game_over:
            return not spinner.is_right_clicked()
        
        self.time += dt
        self.bg_wave += dt * 0.5
        
        # Pause
        if spinner.is_right_clicked() and not self.paused:
            self.paused = True
            return True
        
        if self.paused:
            if spinner.is_left_clicked():
                if self.synth:
                    self.synth.create_back().play()
                self.game_over = True
                return False
            if spinner.is_right_clicked():
                self.paused = False
                if self.synth:
                    self.synth.create_select().play()
            return True
        
        # Animazioni
        if self.roll_animation > 0:
            self.roll_animation -= dt
        
        if self.roll_cooldown > 0:
            self.roll_cooldown -= dt
            if self.roll_cooldown <= 0:
                self.can_roll = True
        
        # === FASE: ROLL ===
        if self.phase == 'roll':
            # Spinner LENTO per lanciare (serve più rotazione)
            if self.can_roll and abs(spinner_delta) > 3:
                self.spinner_accumulator += abs(spinner_delta)/10
                
                if self.spinner_accumulator >= self.spinner_roll_threshold:
                    self.roll_dice()
        
        elif self.phase == 'selecting':
            # ✅ SPINNER NATURALE CON ACCUMULATORE (FLUIDO)
            self.spinner_accumulator += spinner_delta * 0.5  # Moltiplicatore per sensibilità
            
            while abs(self.spinner_accumulator) >= self.spinner_select_threshold:
                direction = 1 if self.spinner_accumulator > 0 else -1
                old = self.selected_die
                self.selected_die = (self.selected_die + direction) % 5
                
                if old != self.selected_die and self.synth:
                    self.synth.create_wall_bounce().play()
                    self.create_particles(90 + self.selected_die * 220 + 70, 420 + 70, (255, 255, 100), 15)
                
                self.spinner_accumulator -= direction * self.spinner_select_threshold  # Rimuovi step consumato
            
            # Sistema click INALTERATO (copia/incolla il resto identico)
            left_pressed = pygame.mouse.get_pressed()[0]
            
            if left_pressed:
                self.left_hold_timer += dt
                
                # Hold completato → CONFERMA
                if self.left_hold_timer >= self.left_hold_threshold:
                    if self.rolls_left > 0 and not all(self.dice_held):
                        self.phase = 'roll'
                    else:
                        self.phase = 'scoring'
                        self.selected_category = 0
                    
                    self.left_hold_timer = 0.0
                    self.click_registered = False
                    if self.synth:
                        self.synth.create_select().play()
                    self.create_particles(640, 620, (100, 255, 255), 35)
                
                elif self.left_hold_timer < 0.2 and not self.click_registered:
                    self.click_registered = True

            else:
                # Rilasciato
                if 0 < self.left_hold_timer < self.left_hold_threshold:
                    if self.click_registered:
                        self.dice_held[self.selected_die] = not self.dice_held[self.selected_die]
                        if self.synth:
                            sound = self.synth.create_powerup() if self.dice_held[self.selected_die] else self.synth.create_hit()
                            sound.play()
                        
                        die_x = 90 + self.selected_die * 220
                        die_y = 420
                        self.create_particles(die_x + 70, die_y + 70, 
                                            (100, 255, 100) if self.dice_held[self.selected_die] else (255, 150, 150), 20)
                        
                        if all(self.dice_held):
                            if self.synth:
                                self.synth.create_select().play()
                
                self.left_hold_timer = 0.0
                self.click_registered = False




                
        elif self.phase == 'scoring':
            # ✅ SPINNER NATURALE CON ACCUMULATORE (FLUIDO - IDENTICO selecting)
            self.spinner_accumulator += spinner_delta * 0.5  # Sensibilità regolabile
            
            while abs(self.spinner_accumulator) >= self.spinner_select_threshold:
                direction = 1 if self.spinner_accumulator > 0 else -1
                old = self.selected_category
                self.selected_category = (self.selected_category + direction) % 13
                
                if old != self.selected_category and self.synth:
                    self.synth.create_wall_bounce().play()
                    # Particelle opzionali per feedback visivo
                    self.create_particles(640, 200 + self.selected_category * 30, (255, 255, 100), 12)
                
                self.spinner_accumulator -= direction * self.spinner_select_threshold
            
            # Click conferma INALTERATO
            if spinner.is_left_clicked():
                cat_id = self.CATEGORIES[self.selected_category][0]
                if cat_id not in self.scores:
                    self.score_category(cat_id)
                    if self.synth:
                        self.synth.create_select().play()
                    self.create_particles(640, 300, (100, 255, 255), 25)
                    # Transizione automatica? self.phase = 'next_turn' o simile

        # Update effects
        for p in self.particles[:]:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] += 500 * dt
            p['life'] -= dt
            if p['life'] <= 0:
                self.particles.remove(p)
        
        for ft in self.floating_texts[:]:
            ft['y'] += ft['vy'] * dt
            ft['life'] -= dt
            if ft['life'] <= 0:
                self.floating_texts.remove(ft)
        
        if self.screen_shake > 0:
            self.screen_shake -= dt
        
        return True
        












    def _dice_used_for_category(self, cat_id, dice):
        """
        Restituisce una lista di 5 booleani che indicano quali dadi contano per la categoria.
        Le regole seguono il gioco Yahtzee.
        """
        from collections import Counter

        counts = Counter(dice)

        # Upper section: Ones-Sixes
        num_map = {
            'ones': 1, 'twos': 2, 'threes': 3,
            'fours': 4, 'fives': 5, 'sixes': 6
        }
        if cat_id in num_map:
            target = num_map[cat_id]
            return [d == target for d in dice]

        # Chance: tutti i dadi contano
        if cat_id == 'chance':
            return [True]*5

        # Three/Four of a kind: evidenzia il numero che massimizza il punteggio
        if cat_id in ['three_kind','four_kind']:
            needed = 3 if cat_id == 'three_kind' else 4
            # trova il numero con almeno 'needed' dadi
            target = None
            for num, cnt in counts.most_common():  # ordina dal più frequente
                if cnt >= needed:
                    target = num
                    break
            return [d == target for d in dice] if target is not None else [False]*5

        # Full House: evidenzia trio + coppia
        if cat_id == 'full_house':
            trio = None
            pair = None
            for num, cnt in counts.items():
                if cnt == 3:
                    trio = num
                elif cnt == 2:
                    pair = num
            if trio is not None and pair is not None:
                return [d == trio or d == pair for d in dice]
            else:
                return [False]*5

        # Small / Large Straight
        if cat_id in ['sm_straight', 'lg_straight']:
            # ordina i dadi unici
            unique = sorted(set(dice))
            # controlla sequenze valide
            straights = [
                [1,2,3,4], [2,3,4,5], [3,4,5,6]  # small
            ]
            if cat_id == 'lg_straight':
                straights = [[1,2,3,4,5],[2,3,4,5,6]]
            # trova la sequenza massima presente
            seq = []
            for s in straights:
                if all(num in unique for num in s):
                    if len(s) > len(seq):
                        seq = s
            # evidenzia i dadi che fanno parte della sequenza
            return [d in seq for d in dice]

        # Yahtzee: tutti e 5 i dadi uguali
        if cat_id == 'yahtzee':
            for num, cnt in counts.items():
                if cnt == 5:
                    return [d == num for d in dice]
            return [False]*5

        # default
        return [False]*5





    def _draw_scorecard(self, surface, sx, sy):
        """Scorecard minimalista con colonna DADI, Upper colorato, senza TOTAL e senza header"""

        card_w, card_h = 780, 320
        x = (1280 - card_w) // 2 + sx
        y = 120 + sy

        pygame.draw.rect(surface, (255,255,255),
                        (x,y,card_w,card_h), border_radius=6)
        pygame.draw.rect(surface, (40,40,40),
                        (x,y,card_w,card_h), 2, border_radius=6)

        # ---- COLUMN POSITIONS ----
        col_cat   = x + 18
        col_desc  = x + 155
        col_dice  = x + 400
        col_score = x + card_w - 120

        # Vertical separators
        for cx in (col_desc-8, col_dice-8, col_score-8):
            pygame.draw.line(surface, (230,230,230),
                            (cx, y+8), (cx, y+card_h-18), 1)

        # ---- ROWS ----
        row_h = 22
        row_y0 = y + 10

        desc_map = {cat_id: name for cat_id, name, _ in self.CATEGORIES}

        for i, (cat_id, cat_name, is_upper) in enumerate(self.CATEGORIES):
            ry = row_y0 + i*row_h

            # alternate rows
            if i%2:
                pygame.draw.rect(surface,(248,248,248),
                                (x+5,ry,card_w-10,row_h))

            # hover
            if self.phase=='scoring' and i==self.selected_category:
                pygame.draw.rect(surface,(220,240,255),
                                (x+5,ry,card_w-10,row_h))
                pygame.draw.rect(surface,(80,140,220),
                                (x+5,ry,card_w-10,row_h),2)

            ty = ry + (row_h - self.font_tiny.get_height())//2

            used = cat_id in self.scores

            # ---- CATEGORY + DESCRIPTION COLORS ----
            if used:
                ccol = dcol = (160,160,160)
            elif i < 6:  # Upper section
                ccol = (40,90,160)
                dcol = (90,120,170)
            else:
                ccol = (70,70,70)
                dcol = (110,110,110)

            # category + description
            surface.blit(self.font_tiny.render(cat_name.upper(),True,ccol),(col_cat,ty))
            surface.blit(self.font_tiny.render(desc_map[cat_id],True,dcol),(col_desc,ty))

            # ---- DICE COLUMN ----
            dice_used = self._dice_used_for_category(cat_id, self.dice)
            dx = col_dice
            for j,val in enumerate(self.dice):
                size = 14
                rect = pygame.Rect(dx + j*(size+4), ry+4, size, size)
                color = (200,60,60) if dice_used[j] else (220,220,220)
                pygame.draw.rect(surface,color,rect,border_radius=3)
                pygame.draw.rect(surface,(120,120,120),rect,1,border_radius=3)

                # pip = valore del dado
                pip = self.font_tiny.render(str(val),True,(30,30,30))
                surface.blit(pip,(rect.centerx-pip.get_width()//2,
                                rect.centery-pip.get_height()//2))

            # ---- SCORE BOX ----
            if used:
                pts = self.scores[cat_id]
                fg,bg = (20,120,20),(235,250,235)
            else:
                pts = self.calculate_score(cat_id,self.dice)
                fg = (0,90,180) if pts>0 else (170,170,170)
                bg = (246,248,250)

            box = pygame.Rect(col_score, ry+3, 70, row_h-6)
            pygame.draw.rect(surface,bg,box,border_radius=4)
            pygame.draw.rect(surface,fg,box,1,border_radius=4)
            txt = self.font_tiny.render(str(pts),True,fg)
            surface.blit(txt,(box.centerx-txt.get_width()//2,ty))

        # ---- BONUS ----
        by = row_y0 + len(self.CATEGORIES)*row_h + 4
        pygame.draw.line(surface,(180,180,180),
                        (x+12,by),(x+card_w-12,by),1)

        if self.upper_bonus:
            b = self.font_tiny.render(f"UPPER BONUS +{self.upper_bonus}",True,(50,50,50))
            surface.blit(b,(x+card_w//2-b.get_width()//2,by+4))





    def _draw_background(self, surface):
        w, h = 1280, 720
        theme_id = self.turn % 13
        
        if theme_id == 0:  # NEON GRID (cyberpunk)
            surface.fill((5, 5, 15))
            for y in range(h):
                t = y / h
                r = int(10 + 40 * t)
                g = int(5 + 10 * t)
                b = int(40 + 120 * t)
                pygame.draw.line(surface, (r, g, b), (0, y), (w, y))
            
            horizon_y = int(h * 0.45)
            spacing = 40
            for i in range(1, 20):
                y = horizon_y + i * spacing
                col = (80, 200, 255)
                pygame.draw.line(surface, col, (0, y), (w, y), 1)
            
            for i in range(-10, 11):
                x = w // 2 + i * spacing
                pygame.draw.line(surface, (80, 200, 255), (x, h), (w // 2 + i * 10, horizon_y), 1)
            
            radius = 80 + int(math.sin(self.bg_wave * 0.7) * 6)
            pygame.draw.circle(surface, (255, 140, 200), (w // 2, horizon_y - 60), radius, 4)
            
            for _ in range(30):
                x = random.randint(0, w)
                y = random.randint(0, horizon_y)
                pulse = 100 + int(155 * abs(math.sin(self.bg_wave + x * 0.01)))
                pygame.draw.circle(surface, (pulse, pulse//2, 255), (x, y), 1)
        
        elif theme_id == 1:  # SPAZIO PROFONDO
            surface.fill((4, 6, 12))
            for y in range(h):
                t = y / h
                r = int(10 + 40 * (1 - t))
                g = int(10 + 20 * t)
                b = int(30 + 80 * t)
                pygame.draw.line(surface, (r, g, b), (0, y), (w, y))
            
            random.seed(1234)
            for _ in range(180):
                x = random.randint(0, w - 1)
                y = random.randint(0, h - 1)
                twinkle = 0.2 + 0.8 * (0.5 + 0.5 * math.sin(self.bg_wave*2 + x*0.01 + y*0.02))
                c = int(150 * twinkle)
                pygame.draw.circle(surface, (c, c, c), (x, y), 1)
            
            for cx, cy, col in [(w*0.2, h*0.3, (80, 40, 150)), (w*0.8, h*0.6, (150, 40, 100))]:
                for r in range(100, 10, -8):
                    alpha = int(60 * (r/100))
                    pygame.draw.circle(surface, col, (int(cx), int(cy)), r, 2)
        
        elif theme_id == 2:  # GRADIENT MORBIDO + PARTICELLE
            for y in range(h):
                t = y / h
                wave = math.sin(self.bg_wave + t * 6) * 0.1
                r = int(20 + 60 * (t + wave))
                g = int(30 + 80 * (1 - t + wave))
                b = int(50 + 90 * t)
                pygame.draw.line(surface, (r, g, b), (0, y), (w, y))
            
            random.seed(5678)
            for i in range(60):
                base_x = random.randint(0, w)
                base_y = random.randint(0, h)
                off_y = int(math.sin(self.bg_wave*0.8 + i*0.3) * 10)
                size = 2 + (i % 3)
                pygame.draw.circle(surface, (200, 230, 255), (base_x, base_y + off_y), size, 1)
        
        elif theme_id == 3:  # LAVA/FUOCO
            for y in range(h):
                t = y / h
                wave = math.sin(self.bg_wave*1.5 + y * 0.01) * 0.15
                r = int(120 + 135 * (t + wave))
                g = int(20 + 60 * (1 - t))
                b = int(5)
                pygame.draw.line(surface, (min(255, r), max(0, g), b), (0, y), (w, y))
            
            random.seed(3333)
            for _ in range(40):
                x = random.randint(0, w)
                y = random.randint(int(h*0.6), h)
                off = int(math.sin(self.bg_wave*2 + x*0.02) * 30)
                col = (255, random.randint(100, 200), 0)
                pygame.draw.circle(surface, col, (x, y + off), random.randint(3, 8))
            
            for i in range(0, w, 80):
                x = i + int(math.sin(self.bg_wave + i*0.01) * 20)
                pygame.draw.line(surface, (255, 150, 0), (x, int(h*0.7)), (x + 40, h), 2)
        
        elif theme_id == 4:  # FORESTA MISTICA (verde)
            for y in range(h):
                t = y / h
                r = int(10 + 30 * t)
                g = int(40 + 80 * t)
                b = int(20 + 40 * t)
                pygame.draw.line(surface, (r, g, b), (0, y), (w, y))
            
            random.seed(4444)
            for _ in range(100):
                x = random.randint(0, w)
                y = random.randint(0, h)
                pulse = 0.5 + 0.5 * math.sin(self.bg_wave + x*0.02)
                col = (50, int(150 * pulse), 80)
                pygame.draw.circle(surface, col, (x, y), random.randint(1, 3))
            
            for i in range(15):
                x = i * 85
                height = random.randint(200, 400)
                for h_seg in range(0, height, 10):
                    y = h - h_seg
                    width = 15 + int(math.sin(self.bg_wave*0.5 + h_seg*0.1) * 8)
                    pygame.draw.circle(surface, (20, 100, 40), (x, y), width//2)
        
        elif theme_id == 5:  # TECH CIRCUITI (matrix verde)
            surface.fill((0, 8, 0))
            for y in range(h):
                t = y / h
                g = int(10 + 40 * t)
                pygame.draw.line(surface, (0, g, 0), (0, y), (w, y))
            
            random.seed(5555)
            for _ in range(50):
                x1, y1 = random.randint(0, w), random.randint(0, h)
                x2, y2 = x1 + random.randint(-100, 100), y1 + random.randint(-100, 100)
                pulse = int(100 + 155 * abs(math.sin(self.bg_wave + x1*0.01)))
                pygame.draw.line(surface, (0, pulse, 0), (x1, y1), (x2, y2), 1)
                pygame.draw.circle(surface, (0, 255, 0), (x1, y1), 3, 1)
            
            for i in range(0, w, 40):
                x = i
                for j in range(0, h, 40):
                    brightness = int(50 + 50 * math.sin(self.bg_wave + i*0.01 + j*0.01))
                    pygame.draw.rect(surface, (0, brightness, 0), (x, j, 2, 2))
        
        elif theme_id == 6:  # OCEANO PROFONDO
            for y in range(h):
                t = y / h
                wave = math.sin(self.bg_wave + y * 0.008) * 0.1
                r = int(5 + 20 * t)
                g = int(40 + 80 * (t + wave))
                b = int(100 + 155 * t)
                pygame.draw.line(surface, (r, min(255, g), b), (0, y), (w, y))
            
            random.seed(6666)
            for _ in range(80):
                x = random.randint(0, w)
                y = random.randint(0, h)
                off_x = int(math.sin(self.bg_wave*0.5 + y*0.01) * 30)
                off_y = int(math.cos(self.bg_wave*0.3 + x*0.01) * 20)
                size = random.randint(2, 5)
                pygame.draw.circle(surface, (100, 180, 255), (x + off_x, y + off_y), size, 1)
            
            for i in range(0, w, 100):
                x = i + int(math.sin(self.bg_wave + i*0.01) * 40)
                y = int(h * 0.3) + int(math.cos(self.bg_wave*0.8 + i*0.02) * 50)
                pygame.draw.circle(surface, (50, 150, 200), (x, y), 20, 2)
        
        elif theme_id == 7:  # AURORA BOREALE
            for y in range(h):
                t = y / h
                r = int(10 + 40 * (1-t))
                g = int(5 + 30 * t)
                b = int(20 + 60 * t)
                pygame.draw.line(surface, (r, g, b), (0, y), (w, y))
            
            for band in range(4):
                base_y = int(h * (0.2 + band * 0.15))
                for x in range(0, w, 5):
                    wave1 = math.sin(self.bg_wave*0.8 + x*0.01 + band)
                    wave2 = math.cos(self.bg_wave*0.5 + x*0.015 + band*0.5)
                    y = base_y + int(wave1 * 60 + wave2 * 40)
                    if band % 2 == 0:
                        col = (100, int(200 + 55*wave1), 150)
                    else:
                        col = (150, int(100 + 55*wave2), 255)
                    pygame.draw.circle(surface, col, (x, y), 3)
            
            random.seed(7777)
            for _ in range(120):
                x = random.randint(0, w)
                y = random.randint(0, int(h*0.5))
                pygame.draw.circle(surface, (200, 200, 220), (x, y), 1)
        
        elif theme_id == 8:  # DESERTO TRAMONTO
            for y in range(h):
                t = y / h
                if t < 0.5:
                    r = int(255 - 50 * t)
                    g = int(180 - 100 * t)
                    b = int(100 - 80 * t)
                else:
                    r = int(200 - 150 * (t-0.5))
                    g = int(120 - 80 * (t-0.5))
                    b = int(40 + 40 * (t-0.5))
                pygame.draw.line(surface, (r, g, b), (0, y), (w, y))
            
            sun_y = int(h * 0.35)
            for r in range(100, 20, -5):
                intensity = (100 - r) / 80
                col = (255, int(200 - 100*intensity), int(50 - 50*intensity))
                pygame.draw.circle(surface, col, (w//2, sun_y), r)
            
            random.seed(8888)
            dune_points = []
            for i in range(0, w, 30):
                y = int(h*0.6) + int(math.sin(self.bg_wave*0.3 + i*0.01) * 40)
                dune_points.append((i, y))
            for i in range(len(dune_points)-1):
                pygame.draw.line(surface, (140, 100, 50), dune_points[i], dune_points[i+1], 3)
        
        elif theme_id == 9:  # TEMPESTA ELETTRICA (viola)
            for y in range(h):
                t = y / h
                wave = math.sin(self.bg_wave*2 + y*0.01) * 0.1
                r = int(40 + 60 * (t + wave))
                g = int(10 + 30 * t)
                b = int(60 + 100 * (t + wave))
                pygame.draw.line(surface, (min(255, r), g, min(255, b)), (0, y), (w, y))
            
            random.seed(9999)
            for _ in range(8):
                x = random.randint(100, w-100)
                y_start = random.randint(0, int(h*0.3))
                segments = random.randint(5, 10)
                curr_x, curr_y = x, y_start
                flash = int(200 + 55 * math.sin(self.bg_wave*5))
                for seg in range(segments):
                    next_x = curr_x + random.randint(-30, 30)
                    next_y = curr_y + random.randint(40, 80)
                    pygame.draw.line(surface, (flash, flash, 255), (curr_x, curr_y), (next_x, next_y), 3)
                    curr_x, curr_y = next_x, next_y
                    if curr_y > h:
                        break
            
            for _ in range(40):
                x = random.randint(0, w)
                y = random.randint(0, h)
                pulse = 100 + int(155 * abs(math.sin(self.bg_wave*3 + x*0.02)))
                pygame.draw.circle(surface, (pulse, pulse//2, 255), (x, y), 2)
        
        elif theme_id == 10:  # CRISTALLI GHIACCIO
            for y in range(h):
                t = y / h
                r = int(180 + 75 * t)
                g = int(220 + 35 * t)
                b = 255
                pygame.draw.line(surface, (r, g, b), (0, y), (w, y))
            
            random.seed(10101)
            for _ in range(25):
                cx = random.randint(50, w-50)
                cy = random.randint(50, h-50)
                size = random.randint(30, 80)
                rotation = self.bg_wave*0.5 + cx*0.01
                for angle in range(0, 360, 60):
                    rad = math.radians(angle + rotation * 50)
                    x1 = cx + int(math.cos(rad) * size)
                    y1 = cy + int(math.sin(rad) * size)
                    pygame.draw.line(surface, (150, 200, 255), (cx, cy), (x1, y1), 2)
                    pygame.draw.circle(surface, (200, 230, 255), (x1, y1), 5)
            
            for _ in range(100):
                x = random.randint(0, w)
                y = random.randint(0, h)
                sparkle = int(150 + 105 * abs(math.sin(self.bg_wave*4 + x*0.01)))
                pygame.draw.circle(surface, (sparkle, sparkle, 255), (x, y), 1)
        
        elif theme_id == 11:  # PSICHEDELICO
            for y in range(h):
                t = y / h
                wave1 = math.sin(self.bg_wave + t * 10) * 0.5
                wave2 = math.cos(self.bg_wave*1.3 + t * 8) * 0.5
                r = int(128 + 127 * wave1)
                g = int(128 + 127 * wave2)
                b = int(128 + 127 * math.sin(self.bg_wave*0.7 + t*12))
                pygame.draw.line(surface, (r, g, b), (0, y), (w, y))
            
            for ring in range(1, 8):
                radius = ring * 60 + int(math.sin(self.bg_wave + ring) * 20)
                hue = (self.bg_wave*30 + ring*45) % 360
                r = int(128 + 127 * math.sin(math.radians(hue)))
                g = int(128 + 127 * math.sin(math.radians(hue + 120)))
                b = int(128 + 127 * math.sin(math.radians(hue + 240)))
                pygame.draw.circle(surface, (r, g, b), (w//2, h//2), radius, 3)
            
            random.seed(11111)
            for _ in range(60):
                x = random.randint(0, w)
                y = random.randint(0, h)
                col = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
                size = 2 + int(3 * abs(math.sin(self.bg_wave + x*0.01)))
                pygame.draw.circle(surface, col, (x, y), size)
        
        else:  # theme_id == 12: MINIMALISTA SCURO
            surface.fill((12, 18, 32))
            for y in range(0, 720, 3):
                wave = math.sin(self.bg_wave + y * 0.006) * 12
                r = int(12 + wave)
                g = int(18 + wave * 0.9)
                b = int(32 + wave * 1.1)
                pygame.draw.line(surface, (max(0,r), max(0,g), max(0,b)), (0, y), (1280, y), 3)










    def draw(self, surface: pygame.Surface):
        shake_x, shake_y = 0, 0
        if self.screen_shake > 0:
            shake_x = random.randint(-6, 6)
            shake_y = random.randint(-6, 6)
        
        self._draw_background(surface)
        self._draw_hud(surface)
        self._draw_scorecard(surface, shake_x, shake_y)
        self._draw_phase_indicator(surface)
        self._draw_dice(surface, shake_x, shake_y)
        self._draw_particles(surface, shake_x, shake_y)
        self._draw_floating_texts(surface)
        
        if self.paused:
            self._draw_pause(surface)
        elif self.game_over:
            self._draw_game_over(surface)
    





    def _draw_hud(self, surface):
        turn = self.font_small.render(f"Turn {self.turn+1}/13", True, (180, 200, 255))
        surface.blit(turn, (25, 20))
        
        rolls_col = (120, 255, 120) if self.rolls_left > 0 else (255, 120, 120)
        rolls = self.font_small.render(f"Rolls: {self.rolls_left}/3", True, rolls_col)
        surface.blit(rolls, (25, 48))
        
        score = self.font_large.render(f"SCORE: {self.score}", True, (255, 255, 100))
        surface.blit(score, (640 - score.get_width()//2, 18))
            







    def _draw_phase_indicator(self, surface):
        """Indicatore fase IN ALTO subito sotto score"""
        y = 75  # Posizione sotto SCORE (18+48+gap=~75px)
        
        if self.phase == 'roll':
            txt = "SPIN TO ROLL DICE"
            col = (100, 255, 255)
        elif self.phase == 'selecting':
            txt = "SPIN: SELECT • CLICK: TOGGLE • HOLD 2.5s: CONFIRM"
            col = (255, 200, 100)
        else:
            txt = "SPIN: SELECT CATEGORY • CLICK: CONFIRM"
            col = (255, 150, 255)
        
        text_surf = self.font_small.render(txt, True, col)
        surface.blit(text_surf, (640 - text_surf.get_width()//2, y))










    def draw_roll_the_dice(self, surface):
        """ROLL THE DICE! screen PRO: testo fumetto + 3 dadi rotanti luminosi"""

        # Background gradient roll (nero->blu scuro per profondità arcade)
        grad = pygame.Surface((1280, 720))
        for y in range(720):
            alpha = int(255 * (y / 720))
            col = (10, 10 + alpha // 4, 20 + alpha // 2)
            pygame.draw.line(grad, col, (0, y), (1280, y))
        surface.blit(grad, (0, 0))

        # Testo principale
        pulse = abs(math.sin(self.time * 6)) * 0.25 + 0.75
        bounce = abs(math.sin(self.time * 4)) * 0.15
        hue_speed = self.time * 0.08

        text = "ROLL THE DICE!"
        base_font = self.font_huge
        textsurf = base_font.render(text, True, (255, 255, 255))
        w, h = textsurf.get_size()

        scale = 1.4 + pulse * 0.3 + bounce * 0.15
        scaled_w = int(w * scale)
        scaled_h = int(h * scale)

        num_chars = len(text)
        color_surfs = []
        for i, char in enumerate(text):
            hue = (hue_speed + i / num_chars * 2) % 1.0
            value = 0.98 + pulse * 0.02

            hue2 = hue * 6.0
            sector = int(hue2)
            f = hue2 - sector
            p = value * (1 - 1)
            q = value * (1 - f * 1)
            t = value * (1 - (1 - f) * 1)

            if sector == 0:
                rgb = (value, t, p)
            elif sector == 1:
                rgb = (q, value, p)
            elif sector == 2:
                rgb = (p, value, t)
            elif sector == 3:
                rgb = (p, q, value)
            elif sector == 4:
                rgb = (t, p, value)
            else:
                rgb = (value, p, q)

            char_color = tuple(int(255 * c) for c in rgb)
            char_surf = base_font.render(char, True, char_color)
            color_surfs.append((char_surf, char_color))

        border_width = 3
        final_surf = pygame.Surface(
            (scaled_w + border_width * 4, scaled_h + border_width * 4),
            pygame.SRCALPHA
        )

        # Bordi glow multi-layer
        border_offsets = [
            (-border_width - 1, 0),
            (border_width + 1, 0),
            (0, -border_width - 1),
            (0, border_width + 1),
        ]
        glow_colors = [(40, 40, 60), (100, 150, 255), (255, 100, 150)]
        for glow_idx, (dx, dy) in enumerate(border_offsets * 2):
            if glow_idx < len(glow_colors) * 2:
                col = glow_colors[glow_idx % len(glow_colors)]
            else:
                col = (20, 20, 20)
            bx = border_width * 2 + dx
            by = border_width * 2 + dy
            for j, (char_surf, _) in enumerate(color_surfs):
                char_w = int(char_surf.get_width() * scale)
                pos_x = bx + sum(int(cs.get_width() * scale) for cs, _ in color_surfs[:j])
                pos_y = by
                scaled_border = pygame.transform.scale(
                    char_surf, (char_w, int(char_surf.get_height() * scale))
                )
                final_surf.blit(scaled_border, (pos_x, pos_y))

        # Testo centrato
        cx, cy = border_width * 2, border_width * 2
        for j, (char_surf, _) in enumerate(color_surfs):
            char_w = int(char_surf.get_width() * scale)
            char_h = int(char_surf.get_height() * scale)
            pos_x = cx + sum(int(cs.get_width() * scale) for cs, _ in color_surfs[:j])
            pos_y = cy + (scaled_h - char_h) // 2
            scaled_char = pygame.transform.scale(char_surf, (char_w, char_h))
            final_surf.blit(scaled_char, (pos_x, pos_y))

        final_surf = final_surf.convert_alpha()
        blit_x = 640 - final_surf.get_width() // 2
        blit_y = 280 - final_surf.get_height() // 2 + int(bounce * 30)
        surface.blit(final_surf, (blit_x, blit_y))

        # 3 DADI SFONDO (all'altezza del testo, dietro)
        dice_size = 100
        dice_rot_speed = self.time * 2
        dice_faces = [1, 4, 6]

        for i in range(3):
            # Orbita più ampia e centrata all'altezza del testo (Y ~280-300)
            angle = dice_rot_speed + i * 2.1
            radius = 300 + pulse * 30  # Più larghi per stare sullo sfondo
            dx = math.cos(angle) * radius
            dy = math.sin(angle) * radius * 0.3 + pulse * 15

            dice_x = 640 + dx - dice_size // 2
            # Posizionati esattamente all'altezza del testo centrale
            dice_y = 280 + dy - dice_size // 2

            # Rotazione
            rot = math.sin(self.time * 5 + i) * 360
            dice_surf = self._create_rotated_die(dice_faces[i], dice_size, rot)

            # Glow sottilissimo (quasi invisibile)
            glow_surf = pygame.transform.scale(
                dice_surf, (dice_size + 20, dice_size + 20)
            )
            glow_surf.set_alpha(50)
            surface.blit(glow_surf, (dice_x - 10, dice_y - 10))

            # Ombra leggera
            shadow_surf = pygame.Surface((dice_size, dice_size), pygame.SRCALPHA)
            pygame.draw.ellipse(
                shadow_surf,
                (0, 0, 0, 40),
                (0, dice_size // 2, dice_size, dice_size // 2),
            )
            surface.blit(shadow_surf, (dice_x + 6, dice_y + 8))

            # Dado principale
            surface.blit(dice_surf, (dice_x, dice_y))

        # Particelle sparkle
        for _ in range(8):
            spark_x = 640 + math.sin(self.time * 10 + _) * 400
            spark_y = 200 + math.cos(self.time * 7 + _ * 1.3) * 100
            spark_size = int(4 + math.sin(self.time * 15 + _) * 3)
            col = (255, 255 - int(self.time * 3 % 100), 200)
            pygame.draw.circle(surface, col, (int(spark_x), int(spark_y)), spark_size)


    def _create_rotated_die(self, face, size, rotation):
        """Dado bianco/nero professionale con facce curate"""

        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        margin = int(size * 0.08)
        rect = pygame.Rect(
            margin,
            margin,
            size - margin * 2,
            size - margin * 2,
        )

        # Gradiente glow interno (grigio molto chiaro)
        glow_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (240, 240, 240), rect.inflate(12, 12), border_radius=16)
        glow_surf.set_alpha(60)
        surf.blit(glow_surf, (0, 0))

        # Dado base (bianco puro)
        pygame.draw.rect(surf, (255, 255, 255), rect, border_radius=14)

        # Bordo nero netto
        pygame.draw.rect(surf, (0, 0, 0), rect, width=2, border_radius=14)

        # Dots precisi e simmetrici (neri con highlight 3D)
        dot_size = int(rect.width * 0.15) if face in [4, 5, 6] else int(rect.width * 0.18)
        cx, cy = rect.center
        quarter = int(rect.width * 0.25)

        # Posizioni standard perfette per dado
        dots_pos = {
            1: [(0, 0)],  # Centro
            4: [(-quarter, -quarter), (quarter, -quarter),
                (-quarter, quarter), (quarter, quarter)],  # Angoli
            6: [(-quarter, -rect.height * 0.35), (quarter, -rect.height * 0.35),
                (0, 0),
                (-quarter, rect.height * 0.35), (quarter, rect.height * 0.35)],  # 3 colonne
        }

        for dx, dy in dots_pos.get(face, []):
            dot_rect = pygame.Rect(
                cx + dx - dot_size // 2,
                cy + dy - dot_size // 2,
                dot_size,
                dot_size,
            )
            
            # Dot nero principale
            pygame.draw.ellipse(surf, (15, 15, 15), dot_rect)
            
            # Highlight 3D (luce da sopra-sinistra)
            highlight = dot_rect.inflate(-dot_size * 0.35, -dot_size * 0.35)
            highlight.move_ip(-2, -2)
            pygame.draw.ellipse(surf, (90, 90, 90), highlight)

        # Rotazione smooth
        rotated = pygame.transform.rotate(surf, rotation)
        return rotated.convert_alpha()







    def _draw_dice(self, surface, sx, sy):
        """Progress SOTTO dadi (visibile), istruzioni SOPRA dadi ben disegnate"""
        
        dice_y = 540 + sy  # DADI SPOSTATI: 540-680px (più spazio sopra e sotto)
        

        # PROGRESS BAR SOTTO DADI (più distanziata)
        if self.phase == 'roll' and self.can_roll:
            bar_w, bar_h = 400, 22
            bar_x = 640 - bar_w // 2 + sx
            bar_y = dice_y + 148 + sy
            
            pygame.draw.rect(surface, (30, 35, 50), (bar_x, bar_y, bar_w, bar_h), 0, 12)
            
            progress = min(1.0, self.spinner_accumulator / self.spinner_roll_threshold)
            fill_w = int(bar_w * progress)
            if fill_w > 0:
                if progress < 0.33: col = (255, 100, 100)
                elif progress < 0.66: col = (255, 200, 100)
                else: col = (100, 255, 100)
                pygame.draw.rect(surface, col, (bar_x + 2, bar_y + 2, fill_w - 2, bar_h - 4), 0, 10)
            
            pygame.draw.rect(surface, (130, 140, 170), (bar_x, bar_y, bar_w, bar_h), 2, 12)
            pct_txt = self.font_tiny.render(f"{int(progress*100)}%", True, (255, 255, 255))
            surface.blit(pct_txt, (bar_x + bar_w//2 - pct_txt.get_width()//2, bar_y + 5))

            self.draw_roll_the_dice(surface)


        elif self.phase == 'selecting' and self.left_hold_timer > 0:
            bar_w, bar_h = 420, 24
            bar_x = 640 - bar_w // 2 + sx
            bar_y = dice_y + 148 + sy
            
            pygame.draw.rect(surface, (35, 40, 55), (bar_x, bar_y, bar_w, bar_h), 0, 12)
            
            progress = min(1.0, self.left_hold_timer / self.left_hold_threshold)
            fill_w = int(bar_w * progress)
            grad_col = (100, int(255 - 55*progress), 255)
            pygame.draw.rect(surface, grad_col, (bar_x + 2, bar_y + 2, fill_w - 2, bar_h - 4), 0, 10)
            
            pygame.draw.rect(surface, (140, 150, 180), (bar_x, bar_y, bar_w, bar_h), 2, 12)
            pct_txt = self.font_tiny.render(f"HOLD {int(progress*100)}%", True, (255, 255, 255))
            surface.blit(pct_txt, (bar_x + bar_w//2 - pct_txt.get_width()//2, bar_y + 4))
        
        # DADI centrati (posizione ottimizzata)
        dice_spacing = 200
        start_x = 640 - (4 * dice_spacing // 2) - 70 + sx
        for i in range(5):
            x = start_x + i * dice_spacing
            y = dice_y - 50
            
            rect = pygame.Rect(x, y, 140, 140)
            
            if self.phase == 'selecting' and i == self.selected_die:
                glow_rect = pygame.Rect(x - 8, y - 8, 156, 156)
                pulse = abs(math.sin(self.time * 6)) * 15
                pygame.draw.rect(surface, (255, 255, int(100 + pulse)), glow_rect, 6, 22)
            
            if self.dice_held[i]:
                bg_col = (60, 140, 60); border_col = (100, 240, 100); border_w = 5
            else:
                bg_col = (35, 45, 65); border_col = (70, 85, 110); border_w = 3
            
            pygame.draw.rect(surface, bg_col, rect, 0, 18)
            pygame.draw.rect(surface, border_col, rect, border_w, 18)
            
            if self.dice_held[i]:
                held = self.font_small.render("HELD", True, (180, 255, 180))
                surface.blit(held, (x + 70 - held.get_width()//2, y - 32))
            
            self._draw_die_face(surface, x + 70, y + 70, self.dice[i])
            num = self.font_tiny.render(str(i+1), True, (130, 130, 150))
            surface.blit(num, (x + 10, y + 10))








    def _draw_die_face(self, surface, cx, cy, value):
        pips = {
            1: [(0, 0)],
            2: [(-30, -30), (30, 30)],
            3: [(-30, -30), (0, 0), (30, 30)],
            4: [(-30, -30), (30, -30), (-30, 30), (30, 30)],
            5: [(-30, -30), (30, -30), (0, 0), (-30, 30), (30, 30)],
            6: [(-30, -30), (30, -30), (-30, 0), (30, 0), (-30, 30), (30, 30)]
        }
        for px, py in pips[value]:
            pygame.draw.circle(surface, (255, 255, 255), (int(cx+px), int(cy+py)), 12)
            pygame.draw.circle(surface, (210, 210, 210), (int(cx+px), int(cy+py)), 12, 2)
    





    def _draw_particles(self, surface, sx, sy):
        for p in self.particles:
            alpha = int(255 * (p['life'] / p['max_life']))
            size = int(p['size'])
            surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p['color'], alpha), (size, size), size)
            surface.blit(surf, (int(p['x']-size+sx), int(p['y']-size+sy)))
    
    def _draw_floating_texts(self, surface):
        for ft in self.floating_texts:
            alpha = int(255 * (ft['life'] / 2.5))
            txt = self.font_large.render(ft['text'], True, ft['color'])
            txt.set_alpha(alpha)
            surface.blit(txt, (int(ft['x'] - txt.get_width()//2), int(ft['y'])))
    
    def _draw_pause(self, surface):
        overlay = pygame.Surface((1280, 720))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(210)
        surface.blit(overlay, (0, 0))
        
        txt = self.font_pause.render("PAUSED", True, (255, 255, 255))
        surface.blit(txt, (640 - txt.get_width()//2, 260))
        
        exit_txt = self.font_medium.render("LEFT CLICK - Exit", True, (255, 100, 100))
        cont_txt = self.font_medium.render("RIGHT CLICK - Continue", True, (100, 255, 100))
        surface.blit(exit_txt, (640 - exit_txt.get_width()//2, 400))
        surface.blit(cont_txt, (640 - cont_txt.get_width()//2, 450))
    
    def _draw_game_over(self, surface):
        overlay = pygame.Surface((1280, 720))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(230)
        surface.blit(overlay, (0, 0))
        
        title = self.font_pause.render("GAME OVER!", True, (255, 215, 0))
        surface.blit(title, (640 - title.get_width()//2, 220))
        
        final = self.font_huge.render(f"{self.score}", True, (255, 255, 100))
        surface.blit(final, (640 - final.get_width()//2, 320))
        
        upper = self.font_small.render(f"Upper: {self.upper_total} + Bonus: {self.upper_bonus}", 
                                       True, (190, 190, 255))
        lower = self.font_small.render(f"Lower: {self.lower_total}", True, (190, 190, 255))
        surface.blit(upper, (640 - upper.get_width()//2, 430))
        surface.blit(lower, (640 - lower.get_width()//2, 465))
        
        hint = self.font_small.render("RIGHT CLICK to continue", True, (170, 170, 170))
        surface.blit(hint, (640 - hint.get_width()//2, 580))





























































class SpinDuel(MiniGame):
    """
    SPIN DUEL - Spinner-based arcade combat game

    CONTROLS:
    - Spinner: Rotazione lama (velocità/direzione)
    - Left Click (breve): Parata difensiva
    - Left Click (hold): Carica energia
    - Left Click (release): Colpo potente
    - Right Click: Pausa

    MECHANICS:
    - Blade inertia system (fisica realistica)
    - Energy management (attack/defense)
    - AI opponent with adaptive difficulty
    - Hit detection based on blade speed/angle
    """

    # Stati di gioco
    STATE_INTRO = 'intro'
    STATE_FIGHT = 'fight'
    STATE_ROUND_END = 'round_end'
    STATE_GAME_OVER = 'game_over'
    STATE_PAUSED = 'paused'

    def __init__(self, synth=None):
        """Inizializzazione gioco"""
        self.synth = synth

        # === SPINNER SYSTEM ===
        self.spinner_accumulator = 0.0
        self.spinner_velocity = 0.0  # Velocità attuale spinner (con inerzia)
        self.spinner_angle = 0.0  # Angolo corrente lama (0-360°)
        self.spinner_friction = 0.92  # Decadimento velocità
        self.spinner_sensitivity = 0.08  # Sensibilità input
        self.last_spinner_direction = 1  # Traccia direzione per inversioni

        # === PLAYER BLADE ===
        self.player_x = 400  # Posizione X giocatore
        self.player_y = 360  # Posizione Y giocatore
        self.player_blade_length = 80  # Lunghezza base lama
        self.player_blade_speed = 0.0  # Velocità rotazione lama
        self.player_energy = 100.0  # Energia/vita giocatore
        self.player_max_energy = 100.0
        self.player_charge = 0.0  # Carica attacco potente (0-1)
        self.player_is_parrying = False  # Stato parata
        self.player_parry_cooldown = 0.0  # Cooldown parata
        self.player_stagger = 0.0  # Stun temporaneo da colpo

        # === AI OPPONENT ===
        self.ai_x = 880  # Posizione X AI
        self.ai_y = 360  # Posizione Y AI
        self.ai_blade_length = 80
        self.ai_blade_speed = 0.0
        self.ai_blade_angle = 180.0  # Parte da angolo opposto
        self.ai_energy = 100.0
        self.ai_max_energy = 100.0
        self.ai_state = 'observe'  # observe, attack, defend, feint
        self.ai_timer = 0.0  # Timer per cambio stato
        self.ai_difficulty = 1.0  # Moltiplicatore difficoltà (1.0-3.0)
        self.ai_charge = 0.0
        self.ai_stagger = 0.0

        # === COMBAT SYSTEM ===
        self.click_timer = 0.0  # Timer per hold detection
        self.click_threshold = 0.4  # Tempo per considerare "hold"
        self.is_clicking = False
        self.charge_power_min = 20  # Danno minimo carica
        self.charge_power_max = 40  # Danno massimo carica
        self.parry_window = 0.15  # Finestra temporale parata perfetta
        self.hit_cooldown_player = 0.0  # Cooldown tra colpi
        self.hit_cooldown_ai = 0.0

        # === GAME STATE ===
        self.state = self.STATE_INTRO
        self.round = 1
        self.max_rounds = 3
        self.player_wins = 0
        self.ai_wins = 0
        self.paused = False
        self.game_over = False
        self.score = 0  # Score per MiniGame interface

        # === VISUAL EFFECTS ===
        self.particles = []
        self.floating_texts = []
        self.screen_shake = 0.0
        self.time = 0.0
        self.bg_wave = 0.0
        self.flash_white = 0.0  # Flash schermo su colpo critico
        self.slow_motion = 1.0  # Slow-mo effect (1.0 = normale)

        # === FONTS ===
        self.font_huge = pygame.font.Font(None, 88)
        self.font_large = pygame.font.Font(None, 56)
        self.font_medium = pygame.font.Font(None, 42)
        self.font_small = pygame.font.Font(None, 32)
        self.font_tiny = pygame.font.Font(None, 22)

        self.reset()

    def get_name(self) -> str:
        return "⚔️ SPIN DUEL"

    def get_description(self) -> str:
        return "Spin to fight! Click to parry! Hold to charge!"

    def reset(self):
        """Reset completo gioco"""
        self.score = 0
        self.game_over = False
        self.state = self.STATE_INTRO
        self.round = 1
        self.player_wins = 0
        self.ai_wins = 0
        self.ai_difficulty = 1.0
        self.reset_round()

    def reset_round(self):
        """Reset singolo round"""
        # Player reset
        self.player_energy = self.player_max_energy
        self.player_charge = 0.0
        self.player_is_parrying = False
        self.player_parry_cooldown = 0.0
        self.player_stagger = 0.0
        self.spinner_velocity = 0.0
        self.spinner_angle = 0.0
        self.player_blade_speed = 0.0

        # AI reset
        self.ai_energy = self.ai_max_energy
        self.ai_blade_angle = 180.0
        self.ai_blade_speed = 0.0
        self.ai_state = 'observe'
        self.ai_timer = random.uniform(0.5, 1.5)
        self.ai_charge = 0.0
        self.ai_stagger = 0.0

        # Combat reset
        self.click_timer = 0.0
        self.is_clicking = False
        self.hit_cooldown_player = 0.0
        self.hit_cooldown_ai = 0.0

        # Effects reset
        self.particles = []
        self.floating_texts = []
        self.screen_shake = 0.0
        self.flash_white = 0.0
        self.slow_motion = 1.0

    # ==================== PHYSICS & MOVEMENT ====================

    def update_blade_physics(self, dt: float, spinner_delta: float):
        """Aggiorna fisica lama con inerzia realistica"""
        if self.player_stagger > 0:
            # Giocatore stunned: friction maggiore
            self.spinner_velocity *= 0.85
        else:
            # Input spinner (con sensibilità)
            acceleration = spinner_delta * self.spinner_sensitivity

            # Detect direction change (inversioni brusche)
            current_dir = 1 if spinner_delta > 0 else -1 if spinner_delta < 0 else 0
            if current_dir != 0 and self.last_spinner_direction != 0:
                if current_dir != self.last_spinner_direction:
                    # Inversione brusca: penalità controllo
                    self.spinner_velocity *= 0.6
                    self.create_particles(
                        self.player_x, self.player_y,
                        (255, 150, 0), 15, speed_mult=0.5
                    )
                self.last_spinner_direction = current_dir

            # Applica accelerazione
            self.spinner_velocity += acceleration

            # Friction naturale
            self.spinner_velocity *= self.spinner_friction

        # Clamp velocità massima
        max_vel = 25.0
        self.spinner_velocity = max(-max_vel, min(max_vel, self.spinner_velocity))

        # Aggiorna angolo (la lama continua a girare per inerzia)
        self.spinner_angle += self.spinner_velocity * dt * 60
        self.spinner_angle %= 360

        # Calcola velocità visiva lama (per lunghezza dinamica)
        self.player_blade_speed = abs(self.spinner_velocity)

    def update_ai_blade(self, dt: float):
        """AI blade movement con comportamento adattivo"""
        if self.ai_stagger > 0:
            self.ai_blade_speed *= 0.9
            self.ai_blade_angle += self.ai_blade_speed * dt * 60
            return

        # AI state machine
        if self.ai_timer <= 0:
            # Cambio stato
            player_speed = self.player_blade_speed
            distance = math.sqrt(
                (self.ai_x - self.player_x)**2 + 
                (self.ai_y - self.player_y)**2
            )

            # Decision making basato su contesto
            if self.ai_energy < 30:
                # Bassa energia: più difensivo
                self.ai_state = random.choice(['defend', 'defend', 'observe'])
            elif player_speed > 15 and self.ai_energy > 50:
                # Giocatore veloce: rischia contrattacco
                self.ai_state = random.choice(['attack', 'feint'])
            elif player_speed < 5:
                # Giocatore lento: punisci
                self.ai_state = 'attack'
            else:
                # Normale
                self.ai_state = random.choice(['observe', 'attack', 'defend'])

            self.ai_timer = random.uniform(0.8, 2.0) / self.ai_difficulty

        self.ai_timer -= dt

        # Execute AI behavior
        if self.ai_state == 'attack':
            # Accelera verso giocatore
            target_speed = 15 * self.ai_difficulty
            if self.ai_blade_speed < target_speed:
                self.ai_blade_speed += 30 * dt * self.ai_difficulty

            # Carica se opportuno
            if self.ai_blade_speed > 12 and random.random() < 0.02 * self.ai_difficulty:
                self.ai_charge = min(1.0, self.ai_charge + dt * 2)

        elif self.ai_state == 'defend':
            # Rallenta e prepara parata
            self.ai_blade_speed *= 0.95
            target_speed = 5
            if self.ai_blade_speed < target_speed:
                self.ai_blade_speed += 10 * dt

        elif self.ai_state == 'feint':
            # Finta: accelerazioni random
            if random.random() < 0.1:
                self.ai_blade_speed += random.uniform(-5, 10) * dt * self.ai_difficulty

        else:  # observe
            # Mantiene velocità moderata
            target_speed = 8
            if abs(self.ai_blade_speed - target_speed) > 0.5:
                if self.ai_blade_speed < target_speed:
                    self.ai_blade_speed += 8 * dt
                else:
                    self.ai_blade_speed -= 8 * dt

        # Friction & clamp
        self.ai_blade_speed *= 0.95
        self.ai_blade_speed = max(0, min(22 * self.ai_difficulty, self.ai_blade_speed))

        # Update angle
        self.ai_blade_angle += self.ai_blade_speed * dt * 60
        self.ai_blade_angle %= 360

    # ==================== COMBAT SYSTEM ====================

    def check_collision(self) -> Tuple[bool, float]:
        """
        Controlla collisione lame
        Returns: (hit_detected, hit_power)
        """
        # Calcola posizioni punta lama
        player_blade_len = self.get_dynamic_blade_length(self.player_blade_speed)
        ai_blade_len = self.get_dynamic_blade_length(self.ai_blade_speed)

        player_tip_x = self.player_x + math.cos(math.radians(self.spinner_angle)) * player_blade_len
        player_tip_y = self.player_y + math.sin(math.radians(self.spinner_angle)) * player_blade_len

        ai_tip_x = self.ai_x + math.cos(math.radians(self.ai_blade_angle)) * ai_blade_len
        ai_tip_y = self.ai_y + math.sin(math.radians(self.ai_blade_angle)) * ai_blade_len

        # Distanza punta lama player -> corpo AI
        dist_player_hit = math.sqrt((player_tip_x - self.ai_x)**2 + (player_tip_y - self.ai_y)**2)

        # Distanza punta lama AI -> corpo player
        dist_ai_hit = math.sqrt((ai_tip_x - self.player_x)**2 + (ai_tip_y - self.player_y)**2)

        hit_threshold = 30  # Raggio hit

        # Player colpisce AI
        if dist_player_hit < hit_threshold and self.hit_cooldown_player <= 0:
            power = self.calculate_hit_power(self.player_blade_speed, self.player_charge)
            return ('player_hits', power)

        # AI colpisce Player
        if dist_ai_hit < hit_threshold and self.hit_cooldown_ai <= 0:
            power = self.calculate_hit_power(self.ai_blade_speed, self.ai_charge)
            return ('ai_hits', power)

        return (None, 0)

    def calculate_hit_power(self, blade_speed: float, charge: float) -> float:
        """Calcola danno in base a velocità + carica"""
        base_damage = blade_speed * 0.8  # Scaling da velocità
        charge_bonus = charge * self.charge_power_max
        return base_damage + charge_bonus

    def apply_hit(self, hit_type: str, power: float):
        """Applica danno e effetti colpo"""
        if hit_type == 'player_hits':
            # Giocatore colpisce AI
            if self.ai_state == 'defend' and random.random() < 0.4:
                # AI para (chance basata su stato)
                power *= 0.3
                self.create_floating_text(self.ai_x, self.ai_y - 50, "PARRIED!", (100, 200, 255))
                if self.synth:
                    self.synth.create_wall_bounce().play()
            else:
                # Colpo pieno
                self.ai_stagger = 0.3
                self.screen_shake = 0.4
                if power > 25:
                    self.create_floating_text(self.ai_x, self.ai_y - 50, "CRITICAL!", (255, 100, 100))
                    self.flash_white = 0.3
                    self.slow_motion = 0.5
                    if self.synth:
                        self.synth.create_high_score().play()
                else:
                    if self.synth:
                        self.synth.create_hit().play()

            self.ai_energy -= power
            self.ai_energy = max(0, self.ai_energy)
            self.hit_cooldown_player = 0.5
            self.player_charge = 0.0  # Reset carica dopo colpo

            # Particles
            self.create_particles(self.ai_x, self.ai_y, (255, 50, 50), 40, speed_mult=2.0)
            self.score += int(power * 10)

        elif hit_type == 'ai_hits':
            # AI colpisce giocatore
            if self.player_is_parrying:
                # Giocatore para
                power *= 0.2
                self.create_floating_text(self.player_x, self.player_y - 50, "BLOCKED!", (100, 255, 100))
                self.player_is_parrying = False
                self.player_parry_cooldown = 1.0
                if self.synth:
                    self.synth.create_wall_bounce().play()
            else:
                # Colpo pieno
                self.player_stagger = 0.4
                self.screen_shake = 0.5
                if power > 25:
                    self.flash_white = 0.2
                if self.synth:
                    self.synth.create_hit().play()

            self.player_energy -= power
            self.player_energy = max(0, self.player_energy)
            self.hit_cooldown_ai = 0.5
            self.ai_charge = 0.0

            # Particles
            self.create_particles(self.player_x, self.player_y, (255, 200, 50), 35, speed_mult=1.5)

    def get_dynamic_blade_length(self, speed: float) -> float:
        """Lunghezza lama dinamica basata su velocità"""
        base = 80
        bonus = min(60, speed * 3)  # Max +60px
        return base + bonus

    # ==================== UPDATE LOOP ====================

    def update(self, dt: float, spinner_delta: float, spinner) -> bool:
        """
        Main update loop
        Returns: True se continua, False se esce
        """
        # Adjust dt for slow-motion
        effective_dt = dt * self.slow_motion

        # Slow-motion recovery
        if self.slow_motion < 1.0:
            self.slow_motion = min(1.0, self.slow_motion + dt * 2)

        self.time += dt
        self.bg_wave += dt * 0.5

        # Flash decay
        if self.flash_white > 0:
            self.flash_white -= dt * 2

        # Pause handling
        if spinner.is_right_clicked() and not self.paused and self.state == self.STATE_FIGHT:
            self.paused = True
            if self.synth:
                self.synth.create_select().play()
            return True

        if self.paused:
            if spinner.is_left_clicked():
                # Exit game
                if self.synth:
                    self.synth.create_back().play()
                self.game_over = True
                return False
            if spinner.is_right_clicked():
                # Resume
                self.paused = False
                if self.synth:
                    self.synth.create_select().play()
            return True

        # ===== STATE MACHINE =====

        if self.state == self.STATE_INTRO:
            # Intro screen: click per iniziare
            if spinner.is_left_clicked():
                self.state = self.STATE_FIGHT
                self.reset_round()
                if self.synth:
                    self.synth.create_level_complete().play()
            return True

        elif self.state == self.STATE_FIGHT:
            # Aggiorna cooldowns
            if self.player_stagger > 0:
                self.player_stagger -= dt
            if self.ai_stagger > 0:
                self.ai_stagger -= dt
            if self.player_parry_cooldown > 0:
                self.player_parry_cooldown -= dt
            if self.hit_cooldown_player > 0:
                self.hit_cooldown_player -= dt
            if self.hit_cooldown_ai > 0:
                self.hit_cooldown_ai -= dt

            # Blade physics
            self.update_blade_physics(effective_dt, spinner_delta)
            self.update_ai_blade(effective_dt)

            # Input: Click handling
            left_pressed = pygame.mouse.get_pressed()[0]

            if left_pressed:
                if not self.is_clicking:
                    # Inizio click
                    self.is_clicking = True
                    self.click_timer = 0.0

                    # Parata immediata (se disponibile)
                    if self.player_parry_cooldown <= 0 and self.player_stagger <= 0:
                        self.player_is_parrying = True
                        if self.synth:
                            self.synth.create_powerup().play()

                # Hold: carica attacco
                self.click_timer += dt
                if self.click_timer >= self.click_threshold:
                    self.player_charge = min(1.0, (self.click_timer - self.click_threshold) / 1.5)
                    # Visual feedback carica
                    if int(self.time * 10) % 2 == 0:
                        self.create_particles(self.player_x, self.player_y, (100, 200, 255), 3, speed_mult=0.3)

            else:
                if self.is_clicking:
                    # Release click
                    if self.click_timer < self.click_threshold:
                        # Click breve: parata già eseguita
                        pass
                    else:
                        # Hold rilasciato: colpo potente ready
                        if self.player_charge > 0.5:
                            self.create_floating_text(self.player_x, self.player_y - 70, "CHARGED!", (255, 255, 100))
                            if self.synth:
                                self.synth.create_score_point().play()

                    self.is_clicking = False
                    self.click_timer = 0.0

                # Parata decade dopo breve tempo
                if self.player_is_parrying:
                    self.player_is_parrying = False

            # Collision detection
            hit_result, hit_power = self.check_collision()
            if hit_result:
                self.apply_hit(hit_result, hit_power)

            # Check round end
            if self.player_energy <= 0:
                self.state = self.STATE_ROUND_END
                self.ai_wins += 1
                self.create_floating_text(640, 200, "AI WINS ROUND!", (255, 100, 100))
                if self.synth:
                    self.synth.create_game_over().play()
            elif self.ai_energy <= 0:
                self.state = self.STATE_ROUND_END
                self.player_wins += 1
                self.score += 1000
                self.create_floating_text(640, 200, "PLAYER WINS ROUND!", (100, 255, 100))
                if self.synth:
                    self.synth.create_level_complete().play()

        elif self.state == self.STATE_ROUND_END:
            # Attesa tra round
            if spinner.is_left_clicked():
                if self.player_wins >= 2 or self.ai_wins >= 2:
                    # Fine partita
                    self.state = self.STATE_GAME_OVER
                else:
                    # Prossimo round
                    self.round += 1
                    self.ai_difficulty = min(2.5, 1.0 + self.round * 0.3)
                    self.reset_round()
                    self.state = self.STATE_FIGHT
                if self.synth:
                    self.synth.create_select().play()
            return True

        elif self.state == self.STATE_GAME_OVER:
            if spinner.is_right_clicked():
                return False  # Exit
            return True

        # Update particles & effects
        self.update_particles(dt)
        self.update_floating_texts(dt)
        if self.screen_shake > 0:
            self.screen_shake -= dt

        return True

    # ==================== VISUAL EFFECTS ====================

    def create_particles(self, x: float, y: float, color: tuple, count: int, speed_mult: float = 1.0):
        """Crea particelle esplosive"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(100, 400) * speed_mult
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(0.3, 0.8),
                'max_life': 0.8,
                'color': color,
                'size': random.uniform(3, 10)
            })

    def create_floating_text(self, x: float, y: float, text: str, color: tuple):
        """Testo fluttuante"""
        self.floating_texts.append({
            'x': x, 'y': y, 'text': text, 'color': color,
            'life': 2.0, 'vy': -80
        })

    def update_particles(self, dt: float):
        for p in self.particles[:]:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] += 600 * dt  # Gravity
            p['life'] -= dt
            if p['life'] <= 0:
                self.particles.remove(p)

    def update_floating_texts(self, dt: float):
        for ft in self.floating_texts[:]:
            ft['y'] += ft['vy'] * dt
            ft['life'] -= dt
            if ft['life'] <= 0:
                self.floating_texts.remove(ft)

    # ==================== RENDERING ====================

    def draw(self, surface: pygame.Surface):
        """Main render function"""
        shake_x, shake_y = 0, 0
        if self.screen_shake > 0:
            shake_x = random.randint(-8, 8)
            shake_y = random.randint(-8, 8)

        # Background
        self._draw_background(surface)

        # State-specific rendering
        if self.state == self.STATE_INTRO:
            self._draw_intro(surface)
        elif self.state == self.STATE_FIGHT:
            self._draw_arena(surface, shake_x, shake_y)
            self._draw_fighters(surface, shake_x, shake_y)
            self._draw_hud(surface)
        elif self.state == self.STATE_ROUND_END:
            self._draw_arena(surface, shake_x, shake_y)
            self._draw_fighters(surface, shake_x, shake_y)
            self._draw_hud(surface)
            self._draw_round_end(surface)
        elif self.state == self.STATE_GAME_OVER:
            self._draw_game_over(surface)

        # Effects (always on top)
        self._draw_particles(surface, shake_x, shake_y)
        self._draw_floating_texts(surface)

        # Flash overlay
        if self.flash_white > 0:
            alpha = int(self.flash_white * 150)
            flash = pygame.Surface((1280, 720))
            flash.fill((255, 255, 255))
            flash.set_alpha(alpha)
            surface.blit(flash, (0, 0))

        # Pause overlay
        if self.paused:
            self._draw_pause(surface)

    def _draw_background(self, surface: pygame.Surface):
        """Background dinamico stile arcade"""
        # Gradient scuro con wave
        for y in range(720):
            t = y / 720
            wave = math.sin(self.bg_wave + t * 4) * 0.05
            r = int(15 + 25 * (t + wave))
            g = int(10 + 20 * (1 - t + wave))
            b = int(25 + 40 * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (1280, y))

        # Grid centrale (arena)
        grid_color = (60, 70, 90)
        center_y = 360
        for i in range(-5, 6):
            y = center_y + i * 60 + int(math.sin(self.bg_wave + i * 0.5) * 10)
            alpha = 255 - abs(i) * 30
            if alpha > 0:
                line_surf = pygame.Surface((1280, 2), pygame.SRCALPHA)
                line_surf.fill((*grid_color, alpha))
                surface.blit(line_surf, (0, y))

        # Particles stellate
        random.seed(1234)
        for _ in range(80):
            x = random.randint(0, 1280)
            y = random.randint(0, 720)
            twinkle = 0.3 + 0.7 * abs(math.sin(self.time * 2 + x * 0.01))
            c = int(150 * twinkle)
            pygame.draw.circle(surface, (c, c, c+50), (x, y), 1)

    def _draw_arena(self, surface: pygame.Surface, sx: int, sy: int):
        """Arena di combattimento"""
        # Linea centrale
        center_x = 640
        pygame.draw.line(surface, (80, 100, 130), 
                        (center_x + sx, 100 + sy), (center_x + sx, 620 + sy), 3)

        # Cerchi posizione fighters
        pygame.draw.circle(surface, (70, 90, 120), 
                          (int(self.player_x) + sx, int(self.player_y) + sy), 50, 2)
        pygame.draw.circle(surface, (120, 90, 70), 
                          (int(self.ai_x) + sx, int(self.ai_y) + sy), 50, 2)

    def _draw_fighters(self, surface: pygame.Surface, sx: int, sy: int):
        """Disegna giocatore e AI con lame"""
        # === PLAYER ===
        px, py = int(self.player_x + sx), int(self.player_y + sy)

        # Corpo player (cerchio blu)
        body_color = (100, 150, 255) if self.player_stagger <= 0 else (255, 150, 100)
        pygame.draw.circle(surface, body_color, (px, py), 25)
        pygame.draw.circle(surface, (200, 220, 255), (px, py), 25, 3)

        # Lama player
        blade_len = self.get_dynamic_blade_length(self.player_blade_speed)
        blade_angle_rad = math.radians(self.spinner_angle)
        blade_end_x = px + int(math.cos(blade_angle_rad) * blade_len)
        blade_end_y = py + int(math.sin(blade_angle_rad) * blade_len)

        # Blade glow
        blade_color = (100, 200, 255)
        if self.player_charge > 0.5:
            blade_color = (255, 255, 100)
        blade_width = int(6 + self.player_blade_speed * 0.5)

        # Trail effect
        for i in range(3):
            trail_len = blade_len * (0.7 - i * 0.2)
            trail_angle = blade_angle_rad - i * 0.3 * (1 if self.spinner_velocity > 0 else -1)
            trail_x = px + int(math.cos(trail_angle) * trail_len)
            trail_y = py + int(math.sin(trail_angle) * trail_len)
            alpha = 100 - i * 30
            trail_surf = pygame.Surface((1280, 720), pygame.SRCALPHA)
            pygame.draw.line(trail_surf, (*blade_color, alpha), (px, py), (trail_x, trail_y), blade_width - i * 2)
            surface.blit(trail_surf, (0, 0))

        # Main blade
        pygame.draw.line(surface, blade_color, (px, py), (blade_end_x, blade_end_y), blade_width)
        pygame.draw.circle(surface, (255, 255, 255), (blade_end_x, blade_end_y), 8)

        # Parry indicator
        if self.player_is_parrying:
            shield_surf = pygame.Surface((1280, 720), pygame.SRCALPHA)
            shield_radius = int(40 + math.sin(self.time * 20) * 5)
            pygame.draw.circle(shield_surf, (100, 255, 100, 120), (px, py), shield_radius, 4)
            surface.blit(shield_surf, (0, 0))

        # === AI ===
        ax, ay = int(self.ai_x + sx), int(self.ai_y + sy)

        # Corpo AI (cerchio rosso)
        ai_body_color = (255, 100, 100) if self.ai_stagger <= 0 else (255, 200, 100)
        pygame.draw.circle(surface, ai_body_color, (ax, ay), 25)
        pygame.draw.circle(surface, (255, 150, 150), (ax, ay), 25, 3)

        # Lama AI
        ai_blade_len = self.get_dynamic_blade_length(self.ai_blade_speed)
        ai_blade_angle_rad = math.radians(self.ai_blade_angle)
        ai_blade_end_x = ax + int(math.cos(ai_blade_angle_rad) * ai_blade_len)
        ai_blade_end_y = ay + int(math.sin(ai_blade_angle_rad) * ai_blade_len)

        ai_blade_color = (255, 100, 100)
        if self.ai_charge > 0.5:
            ai_blade_color = (255, 50, 255)
        ai_blade_width = int(6 + self.ai_blade_speed * 0.5)

        # AI blade trail
        for i in range(3):
            trail_len = ai_blade_len * (0.7 - i * 0.2)
            trail_angle = ai_blade_angle_rad - i * 0.3
            trail_x = ax + int(math.cos(trail_angle) * trail_len)
            trail_y = ay + int(math.sin(trail_angle) * trail_len)
            alpha = 100 - i * 30
            trail_surf = pygame.Surface((1280, 720), pygame.SRCALPHA)
            pygame.draw.line(trail_surf, (*ai_blade_color, alpha), (ax, ay), (trail_x, trail_y), ai_blade_width - i * 2)
            surface.blit(trail_surf, (0, 0))

        pygame.draw.line(surface, ai_blade_color, (ax, ay), (ai_blade_end_x, ai_blade_end_y), ai_blade_width)
        pygame.draw.circle(surface, (255, 255, 255), (ai_blade_end_x, ai_blade_end_y), 8)

    def _draw_hud(self, surface: pygame.Surface):
        """HUD con energie, round, score"""
        # Energy bars
        bar_width = 300
        bar_height = 30

        # Player energy (sinistra)
        player_bar_x = 50
        player_bar_y = 50
        pygame.draw.rect(surface, (40, 40, 60), (player_bar_x, player_bar_y, bar_width, bar_height), 0, 8)

        player_fill = int(bar_width * (self.player_energy / self.player_max_energy))
        if player_fill > 0:
            color = (100, 255, 100) if self.player_energy > 50 else (255, 200, 100) if self.player_energy > 25 else (255, 100, 100)
            pygame.draw.rect(surface, color, (player_bar_x + 2, player_bar_y + 2, player_fill - 4, bar_height - 4), 0, 6)

        pygame.draw.rect(surface, (150, 170, 200), (player_bar_x, player_bar_y, bar_width, bar_height), 3, 8)

        player_txt = self.font_small.render("PLAYER", True, (150, 200, 255))
        surface.blit(player_txt, (player_bar_x, player_bar_y - 28))

        energy_txt = self.font_tiny.render(f"{int(self.player_energy)}/100", True, (255, 255, 255))
        surface.blit(energy_txt, (player_bar_x + bar_width//2 - energy_txt.get_width()//2, player_bar_y + 6))

        # AI energy (destra)
        ai_bar_x = 1280 - 50 - bar_width
        ai_bar_y = 50
        pygame.draw.rect(surface, (60, 40, 40), (ai_bar_x, ai_bar_y, bar_width, bar_height), 0, 8)

        ai_fill = int(bar_width * (self.ai_energy / self.ai_max_energy))
        if ai_fill > 0:
            color = (255, 100, 100) if self.ai_energy > 50 else (255, 150, 100) if self.ai_energy > 25 else (200, 100, 100)
            pygame.draw.rect(surface, color, (ai_bar_x + 2, ai_bar_y + 2, ai_fill - 4, bar_height - 4), 0, 6)

        pygame.draw.rect(surface, (200, 150, 150), (ai_bar_x, ai_bar_y, bar_width, bar_height), 3, 8)

        ai_txt = self.font_small.render("AI OPPONENT", True, (255, 150, 150))
        surface.blit(ai_txt, (ai_bar_x + bar_width - ai_txt.get_width(), ai_bar_y - 28))

        ai_energy_txt = self.font_tiny.render(f"{int(self.ai_energy)}/100", True, (255, 255, 255))
        surface.blit(ai_energy_txt, (ai_bar_x + bar_width//2 - ai_energy_txt.get_width()//2, ai_bar_y + 6))

        # Round counter (centro alto)
        round_txt = self.font_medium.render(f"ROUND {self.round}", True, (255, 255, 100))
        surface.blit(round_txt, (640 - round_txt.get_width()//2, 20))

        wins_txt = self.font_small.render(f"P:{self.player_wins}  vs  AI:{self.ai_wins}", True, (200, 200, 200))
        surface.blit(wins_txt, (640 - wins_txt.get_width()//2, 60))

        # Score
        score_txt = self.font_small.render(f"SCORE: {self.score}", True, (255, 255, 255))
        surface.blit(score_txt, (640 - score_txt.get_width()//2, 670))

        # Charge indicator (player)
        if self.player_charge > 0:
            charge_txt = self.font_tiny.render(f"CHARGE: {int(self.player_charge * 100)}%", True, (255, 255, 100))
            surface.blit(charge_txt, (player_bar_x, player_bar_y + 35))

        # Speed indicator
        speed_txt = self.font_tiny.render(f"SPEED: {int(self.player_blade_speed)}", True, (150, 200, 255))
        surface.blit(speed_txt, (player_bar_x, player_bar_y + 55))

    def _draw_intro(self, surface: pygame.Surface):
        """Schermata introduttiva"""
        # Title con effetto
        pulse = abs(math.sin(self.time * 3)) * 0.2 + 0.8
        title = self.font_huge.render("⚔️ SPIN DUEL ⚔️", True, (255, 255, 100))
        title_scale = pygame.transform.scale(title, 
            (int(title.get_width() * pulse), int(title.get_height() * pulse)))
        surface.blit(title_scale, (640 - title_scale.get_width()//2, 150))

        # Subtitle
        subtitle = self.font_medium.render("Master the blade through rotation", True, (200, 200, 255))
        surface.blit(subtitle, (640 - subtitle.get_width()//2, 280))

        # Controls
        y = 360
        controls = [
            "🌀 SPINNER - Control blade rotation & power",
            "🛡️ CLICK (brief) - Parry incoming attacks",
            "⚡ HOLD CLICK - Charge devastating strike",
            "⏸️  RIGHT CLICK - Pause game"
        ]
        for ctrl in controls:
            txt = self.font_small.render(ctrl, True, (180, 220, 255))
            surface.blit(txt, (640 - txt.get_width()//2, y))
            y += 45

        # Start prompt
        start = self.font_large.render("CLICK TO START", True, (100, 255, 100))
        if int(self.time * 2) % 2:
            surface.blit(start, (640 - start.get_width()//2, 600))

    def _draw_round_end(self, surface: pygame.Surface):
        """Overlay fine round"""
        overlay = pygame.Surface((1280, 720))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        surface.blit(overlay, (0, 0))

        if self.player_wins > self.ai_wins:
            txt = self.font_huge.render("VICTORY!", True, (100, 255, 100))
        else:
            txt = self.font_huge.render("DEFEAT", True, (255, 100, 100))
        surface.blit(txt, (640 - txt.get_width()//2, 250))

        continue_txt = self.font_medium.render("Click to continue", True, (200, 200, 200))
        surface.blit(continue_txt, (640 - continue_txt.get_width()//2, 450))

    def _draw_game_over(self, surface: pygame.Surface):
        """Schermata finale"""
        overlay = pygame.Surface((1280, 720))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(220)
        surface.blit(overlay, (0, 0))

        if self.player_wins >= 2:
            title = self.font_huge.render("🏆 CHAMPION! 🏆", True, (255, 215, 0))
        else:
            title = self.font_huge.render("DEFEATED", True, (255, 100, 100))
        surface.blit(title, (640 - title.get_width()//2, 180))

        score = self.font_large.render(f"FINAL SCORE: {self.score}", True, (255, 255, 100))
        surface.blit(score, (640 - score.get_width()//2, 300))

        wins = self.font_medium.render(f"Player {self.player_wins} - {self.ai_wins} AI", True, (200, 200, 200))
        surface.blit(wins, (640 - wins.get_width()//2, 380))

        exit_txt = self.font_small.render("Right Click to Exit", True, (150, 150, 150))
        surface.blit(exit_txt, (640 - exit_txt.get_width()//2, 550))

    def _draw_pause(self, surface: pygame.Surface):
        """Menu pausa"""
        overlay = pygame.Surface((1280, 720))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(200)
        surface.blit(overlay, (0, 0))

        title = self.font_huge.render("⏸️  PAUSED", True, (255, 255, 255))
        surface.blit(title, (640 - title.get_width()//2, 250))

        resume = self.font_medium.render("RIGHT CLICK - Resume", True, (100, 255, 100))
        exit_txt = self.font_medium.render("LEFT CLICK - Exit", True, (255, 100, 100))
        surface.blit(resume, (640 - resume.get_width()//2, 380))
        surface.blit(exit_txt, (640 - exit_txt.get_width()//2, 430))

    def _draw_particles(self, surface: pygame.Surface, sx: int, sy: int):
        """Rendering particles"""
        for p in self.particles:
            alpha = int(255 * (p['life'] / p['max_life']))
            size = int(p['size'])
            surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p['color'], alpha), (size, size), size)
            surface.blit(surf, (int(p['x']-size+sx), int(p['y']-size+sy)))

    def _draw_floating_texts(self, surface: pygame.Surface):
        """Rendering floating text"""
        for ft in self.floating_texts:
            alpha = int(255 * (ft['life'] / 2.0))
            txt = self.font_large.render(ft['text'], True, ft['color'])
            txt.set_alpha(alpha)
            surface.blit(txt, (int(ft['x'] - txt.get_width()//2), int(ft['y'])))


























        
class PongSpinner(MiniGame):
    def __init__(self, synth: SoundSynthesizer):
        super().__init__()
        self.synth = synth
        
        # Paddle setup (orizzontale)
        self.paddle_bottom_x = 640  # Player (bottom)
        self.paddle_top_x = 640     # AI (top)
        self.paddle_width = 120
        self.paddle_height = 15
        
        # NATURAL MOVEMENT - Direct position control - VELOCITA' AUMENTATA
        self.paddle_target_x = 640
        self.paddle_smooth_factor = 18.0  # Aumentato da 12.0 a 18.0
        self.paddle_max_speed = 1500  # Aumentato da 1000 a 1500
        
        # AI settings - SMOOTH
        self.ai_target_x = 640
        self.ai_smooth_speed = 8.0
        
        # Ball setup
        self.ball_x = 640
        self.ball_y = 360
        self.ball_vx = 0
        self.ball_vy = 0
        self.ball_size = 8
        self.ball_trail = []
        self.ball_glow_pulse = 0
        
        # Game state
        self.score_player = 0
        self.score_ai = 0
        self.max_score = 11
        self.rally_count = 0
        self.max_rally = 0
        self.total_hits = 0
        self.perfect_hits = 0
        
        # Combo system
        self.combo_multiplier = 1.0
        self.combo_timer = 0
        self.combo_decay_time = 2.5
        self.last_hit_quality = 0
        
        # Powerup system
        self.active_powerup = None
        self.powerup_timer = 0
        self.powerup_duration = 8.0
        self.powerups_available = []
        self.powerup_spawn_timer = 0
        self.powerup_spawn_interval = 15.0
        
        # Visual effects
        self.particles = []
        self.floating_texts = []
        self.screen_shake = 0
        self.flash_timer = 0
        
        # Background animation
        self.stars = []
        self.wave_lines = []
        self.bg_pulse = 0
        self.time = 0
        
        # Pause system
        self.paused = False
        self.confirm_exit = False
        
        # Stats tracking
        self.match_duration = 0
        self.powerups_collected = 0
        
        self._init_background()
    
    def _init_background(self):
        """Inizializza elementi sfondo animato"""
        for _ in range(100):
            self.stars.append({
                'x': random.randint(0, 1280),
                'y': random.randint(0, 720),
                'size': random.randint(1, 3),
                'speed': random.uniform(20, 80),
                'brightness': random.uniform(0.4, 1.0),
                'twinkle': random.uniform(0, math.pi * 2),
                'layer': random.choice([1, 2, 3])
            })
        
        for i in range(8):
            self.wave_lines.append({
                'y': i * 90 + 45,
                'offset': random.uniform(0, 100),
                'speed': random.uniform(30, 60),
                'amplitude': random.uniform(5, 15)
            })
    
    def get_name(self) -> str:
        return "Pong Spinner"
    
    def get_description(self) -> str:
        return "Tennis-style Pong - First to 11!"
    
    def reset(self):
        """Reset completo del gioco"""
        self.score = 0
        self.game_over = False
        
        # Paddle positions
        self.paddle_bottom_x = 640
        self.paddle_top_x = 640
        self.paddle_target_x = 640
        self.ai_target_x = 640
        
        # Scores
        self.score_player = 0
        self.score_ai = 0
        
        # Rally stats
        self.rally_count = 0
        self.max_rally = 0
        self.total_hits = 0
        self.perfect_hits = 0
        
        # Combo
        self.combo_multiplier = 1.0
        self.combo_timer = 0
        self.last_hit_quality = 0
        
        # Powerups
        self.active_powerup = None
        self.powerup_timer = 0
        self.powerups_available = []
        self.powerup_spawn_timer = 0
        
        # Effects
        self.particles = []
        self.floating_texts = []
        self.screen_shake = 0
        self.flash_timer = 0
        self.ball_trail = []
        
        # Pause
        self.paused = False
        self.confirm_exit = False
        
        # Stats
        self.match_duration = 0
        self.powerups_collected = 0
        self.time = 0
        self.bg_pulse = 0
        
        self._reset_ball()
    
    def _reset_ball(self, direction: int = 0):
        """Reset palla"""
        self.ball_x = 640
        self.ball_y = 360
        self.ball_trail = []
        
        if direction == 0:
            direction = random.choice([-1, 1])
        
        angle_range = 45
        angle = random.uniform(-angle_range, angle_range)
        speed = 450
        
        self.ball_vx = math.sin(math.radians(angle)) * speed
        self.ball_vy = direction * math.cos(math.radians(angle)) * speed
        
        self.rally_count = 0
        self.combo_timer = 0
    
    def _create_particles(self, x: float, y: float, count: int, color: tuple, 
                         speed_min: float = 80, speed_max: float = 250):
        """Sistema particellare avanzato"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(speed_min, speed_max)
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'lifetime': random.uniform(0.3, 1.0),
                'max_lifetime': 1.0,
                'color': color,
                'size': random.randint(2, 6),
                'gravity': random.uniform(100, 300)
            })
    
    def _add_floating_text(self, x: float, y: float, text: str, 
                          color: tuple, size: int = 36):
        """Testi fluttuanti per feedback"""
        self.floating_texts.append({
            'x': x,
            'y': y,
            'text': text,
            'color': color,
            'lifetime': 1.5,
            'max_lifetime': 1.5,
            'vy': -80,
            'size': size
        })
    
    def _spawn_powerup(self):
        """Spawna powerup random"""
        powerup_types = [
            {'type': 'big_paddle', 'color': (100, 200, 255), 'shape': 'rectangle'},
            {'type': 'slow_ball', 'color': (150, 255, 150), 'shape': 'hourglass'},
            {'type': 'multi_ball', 'color': (255, 200, 100), 'shape': 'triple_circle'},
            {'type': 'shield', 'color': (255, 150, 255), 'shape': 'shield'},
            {'type': 'speed_boost', 'color': (255, 255, 100), 'shape': 'lightning'}
        ]
        
        powerup = random.choice(powerup_types).copy()
        powerup['x'] = random.randint(200, 1080)
        powerup['y'] = random.randint(200, 520)
        powerup['pulse'] = 0
        powerup['lifetime'] = 10.0
        powerup['rotation'] = 0
        
        self.powerups_available.append(powerup)
        self.synth.create_blip(2).play()
    
    def _activate_powerup(self, powerup_type: str):
        """Attiva un powerup"""
        self.active_powerup = powerup_type
        self.powerup_timer = self.powerup_duration
        self.powerups_collected += 1
        
        if powerup_type == 'big_paddle':
            self.paddle_width = 180
            self._add_floating_text(640, 300, "BIG PADDLE!", (100, 200, 255), 48)
        elif powerup_type == 'slow_ball':
            self.ball_vx *= 0.6
            self.ball_vy *= 0.6
            self._add_floating_text(640, 300, "SLOW MOTION!", (150, 255, 150), 48)
        elif powerup_type == 'multi_ball':
            self._add_floating_text(640, 300, "MULTI BALL!", (255, 200, 100), 48)
        elif powerup_type == 'shield':
            self._add_floating_text(640, 300, "SHIELD ACTIVE!", (255, 150, 255), 48)
        elif powerup_type == 'speed_boost':
            self.paddle_smooth_factor = 25.0  # Ancora più veloce con powerup
            self._add_floating_text(640, 300, "SPEED UP!", (255, 255, 100), 48)
        
        self.synth.create_high_score().play()
    
    def _deactivate_powerup(self):
        """Disattiva powerup corrente"""
        if self.active_powerup == 'big_paddle':
            self.paddle_width = 120
        elif self.active_powerup == 'speed_boost':
            self.paddle_smooth_factor = 18.0  # Torna alla velocità aumentata base
        
        self.active_powerup = None
        self.synth.create_back().play()
    






    def update(self, dt: float, spinner_delta: float, spinner: SpinnerInput) -> bool:
        """Update loop principale"""
        
        # === GESTIONE PAUSA - PULSANTI INVERTITI ===
        if spinner.is_right_clicked():
            if self.game_over:
                return False
            
            if not self.paused:
                self.paused = True
                self.confirm_exit = True
                self.synth.create_blip(0).play()
            else:
                self.paused = False
                self.confirm_exit = False
                self.synth.create_select().play()
        
        if spinner.is_left_clicked() and self.paused:
            return False
        
        # Update time ed effetti sempre
        self.time += dt
        self.bg_pulse += dt * 1.5
        self.ball_glow_pulse += dt * 8
        
        # Update background
        self._update_background(dt)
        
        # Update particles
        for p in self.particles[:]:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] += p['gravity'] * dt
            p['lifetime'] -= dt
            if p['lifetime'] <= 0:
                self.particles.remove(p)
        
        # Update floating texts
        for txt in self.floating_texts[:]:
            txt['y'] += txt['vy'] * dt
            txt['lifetime'] -= dt
            if txt['lifetime'] <= 0:
                self.floating_texts.remove(txt)
        
        # Update screen effects
        if self.screen_shake > 0:
            self.screen_shake -= dt * 5
        if self.flash_timer > 0:
            self.flash_timer -= dt * 3
        
        # Se in pausa o game over, non aggiornare gameplay
        if self.paused or self.game_over:
            return True
        
        # Update match duration
        self.match_duration += dt
        
        # Update combo timer
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo_multiplier = 1.0
        
        # Update powerup timer
        if self.powerup_timer > 0:
            self.powerup_timer -= dt
            if self.powerup_timer <= 0:
                self._deactivate_powerup()
        
        # Powerup spawn
        self.powerup_spawn_timer += dt
        if self.powerup_spawn_timer >= self.powerup_spawn_interval:
            self._spawn_powerup()
            self.powerup_spawn_timer = 0
        
        # Update powerups
        for pu in self.powerups_available[:]:
            pu['pulse'] += dt * 3
            pu['rotation'] += dt * 120
            pu['lifetime'] -= dt
            if pu['lifetime'] <= 0:
                self.powerups_available.remove(pu)
            elif (abs(self.ball_x - pu['x']) < 20 and 
                abs(self.ball_y - pu['y']) < 20):
                self._activate_powerup(pu['type'])
                self.powerups_available.remove(pu)
                self._create_particles(pu['x'], pu['y'], 30, pu['color'])
        
        # === GAMEPLAY ===
        
        # === MOVIMENTO PADDLE PLAYER - PIU' VELOCE ===
        spinner_sensitivity = 11.0
        self.paddle_target_x += spinner_delta * spinner_sensitivity
        
        self.paddle_target_x = max(self.paddle_width // 2, 
                                min(1280 - self.paddle_width // 2, self.paddle_target_x))
        
        diff = self.paddle_target_x - self.paddle_bottom_x
        max_step = self.paddle_max_speed * dt
        smooth_step = diff * self.paddle_smooth_factor * dt
        
        if abs(smooth_step) > max_step:
            smooth_step = max_step if smooth_step > 0 else -max_step
        
        self.paddle_bottom_x += smooth_step
        
        self.paddle_bottom_x = max(self.paddle_width // 2, 
                                min(1280 - self.paddle_width // 2, self.paddle_bottom_x))
        
        # === AI MOVEMENT SMOOTH ===
        # Costanti per paddle positions
        EDGE_DISTANCE = 30
        paddle_y_top = EDGE_DISTANCE
        paddle_y_bottom = 720 - EDGE_DISTANCE - self.paddle_height
        
        if self.ball_vy < 0:
            # Ball going towards AI
            predict_time = abs((paddle_y_top + self.paddle_height - self.ball_y) / self.ball_vy) if self.ball_vy != 0 else 0
            self.ai_target_x = self.ball_x + self.ball_vx * predict_time
        else:
            # Ball going away, return to center
            self.ai_target_x = 640
        
        self.ai_target_x = max(self.paddle_width // 2, 
                            min(1280 - self.paddle_width // 2, self.ai_target_x))
        
        diff_ai = self.ai_target_x - self.paddle_top_x
        
        if abs(diff_ai) > 3:
            ai_difficulty = min(1.3, 1.0 + (self.score_ai * 0.05))
            self.paddle_top_x += diff_ai * self.ai_smooth_speed * ai_difficulty * dt
        
        self.paddle_top_x = max(self.paddle_width // 2, 
                            min(1280 - self.paddle_width // 2, self.paddle_top_x))
        
        # Ball movement
        self.ball_x += self.ball_vx * dt
        self.ball_y += self.ball_vy * dt
        
        # Ball trail
        self.ball_trail.append((self.ball_x, self.ball_y))
        if len(self.ball_trail) > 15:
            self.ball_trail.pop(0)
        
        # Wall collision
        if self.ball_x <= self.ball_size or self.ball_x >= 1280 - self.ball_size:
            self.ball_vx *= -1.02
            self.ball_x = max(self.ball_size, min(1280 - self.ball_size, self.ball_x))
            self.synth.create_blip(0).play()
            self._create_particles(self.ball_x, self.ball_y, 8, (100, 150, 200))
        
        # === PADDLE COLLISION - BOTTOM (player) - FIXED SYMMETRIC ===
        if (paddle_y_bottom <= self.ball_y <= paddle_y_bottom + self.paddle_height + self.ball_size and
            self.paddle_bottom_x - self.paddle_width // 2 <= self.ball_x <= 
            self.paddle_bottom_x + self.paddle_width // 2):
            
            offset_from_center = abs(self.ball_x - self.paddle_bottom_x) / (self.paddle_width // 2)
            hit_quality = 1.0 - offset_from_center
            self.last_hit_quality = hit_quality
            
            if hit_quality > 0.9:
                self.perfect_hits += 1
                self._add_floating_text(self.ball_x, self.ball_y - 30, "PERFECT!", (255, 255, 100), 32)
                self.score += 25
            
            offset = (self.ball_x - self.paddle_bottom_x) / (self.paddle_width // 2)
            max_angle = 60
            angle = offset * max_angle
            
            speed = math.sqrt(self.ball_vx**2 + self.ball_vy**2) * 1.04
            speed = min(speed, 800)
            
            self.ball_vx = math.sin(math.radians(angle)) * speed
            self.ball_vy = -abs(math.cos(math.radians(angle)) * speed)
            
            self.rally_count += 1
            self.total_hits += 1
            self.max_rally = max(self.max_rally, self.rally_count)
            
            self.combo_timer = self.combo_decay_time
            self.combo_multiplier = min(3.0, 1.0 + (self.rally_count * 0.1))
            
            base_score = 15
            rally_bonus = self.rally_count * 3
            combo_score = int((base_score + rally_bonus) * self.combo_multiplier)
            self.score += combo_score
            
            self.synth.create_hit().play()
            self.screen_shake = 0.2
            self._create_particles(self.ball_x, self.ball_y, 15, (100, 255, 150))
            
            if self.rally_count % 5 == 0:
                self._add_floating_text(640, 360, f"RALLY x{self.rally_count}!", (255, 200, 100), 42)
        
        # === PADDLE COLLISION - TOP (AI) - FIXED SYMMETRIC ===
        if (paddle_y_top - self.ball_size <= self.ball_y <= paddle_y_top + self.paddle_height and
            self.paddle_top_x - self.paddle_width // 2 <= self.ball_x <= 
            self.paddle_top_x + self.paddle_width // 2):
            
            offset = (self.ball_x - self.paddle_top_x) / (self.paddle_width // 2)
            max_angle = 60
            angle = offset * max_angle
            
            speed = math.sqrt(self.ball_vx**2 + self.ball_vy**2) * 1.04
            speed = min(speed, 800)
            
            self.ball_vx = math.sin(math.radians(angle)) * speed
            self.ball_vy = abs(math.cos(math.radians(angle)) * speed)
            
            self.rally_count += 1
            self.max_rally = max(self.max_rally, self.rally_count)
            
            self.synth.create_blip(1).play()
            self._create_particles(self.ball_x, self.ball_y, 12, (255, 120, 120))
        
        # Goal - AI scores (ball passes player paddle)
        if self.ball_y >= 720 + 20:
            if self.active_powerup == 'shield':
                self._reset_ball(-1)
                self._deactivate_powerup()
                self._add_floating_text(640, 600, "SHIELD SAVED!", (255, 150, 255), 48)
                self.synth.create_high_score().play()
            else:
                self.score_ai += 1
                self.synth.create_back().play()
                self._create_particles(640, 720, 40, (255, 100, 100), 150, 400)
                self.flash_timer = 1.0
                
                if self.score_ai >= self.max_score:
                    self.game_over = True
                    self.synth.create_game_over().play()
                else:
                    self._reset_ball(-1)
        
        # Goal - Player scores (ball passes AI paddle)
        if self.ball_y <= -20:
            self.score_player += 1
            goal_bonus = 150 + (self.rally_count * 25)
            self.score += goal_bonus
            
            self.synth.create_score_point().play()
            self._create_particles(640, 0, 40, (100, 255, 150), 150, 400)
            self._add_floating_text(640, 100, f"+{goal_bonus} GOAL!", (255, 255, 100), 52)
            self.flash_timer = 0.5
            
            if self.score_player >= self.max_score:
                self.game_over = True
                self.score += 1000
                self.synth.create_high_score().play()
            else:
                self._reset_ball(1)
        
        return True







    def _update_background(self, dt: float):
        """Aggiorna animazioni background"""
        for star in self.stars:
            star['y'] += star['speed'] * star['layer'] * dt
            if star['y'] > 720:
                star['y'] = -10
                star['x'] = random.randint(0, 1280)
            star['twinkle'] += dt * 3
        
        for wave in self.wave_lines:
            wave['offset'] += wave['speed'] * dt
            if wave['offset'] > 100:
                wave['offset'] = 0
    
    def draw(self, surface: pygame.Surface):
        """Rendering completo"""
        
        # Background gradiente
        for y in range(720):
            factor = y / 720
            pulse = abs(math.sin(self.bg_pulse * 0.3)) * 10
            r = int(5 + factor * 8 + pulse)
            g = int(10 + factor * 12 + pulse)
            b = int(25 + factor * 20 + pulse)
            pygame.draw.line(surface, (r, g, b), (0, y), (1280, y))
        
        # Stars
        for star in self.stars:
            brightness = int(star['brightness'] * 255)
            twinkle = abs(math.sin(star['twinkle'])) * 0.4 + 0.6
            alpha = int(brightness * twinkle * (0.3 + star['layer'] * 0.2))
            
            if star['size'] == 1:
                try:
                    surface.set_at((int(star['x']), int(star['y'])), (alpha, alpha, alpha + 30))
                except:
                    pass
            else:
                pygame.draw.circle(surface, (alpha, alpha, min(255, alpha + 40)), 
                                 (int(star['x']), int(star['y'])), star['size'])
        
        # Wave lines
        for wave in self.wave_lines:
            points = []
            for x in range(0, 1281, 40):
                offset_y = math.sin((x + wave['offset']) * 0.02) * wave['amplitude']
                points.append((x, wave['y'] + offset_y))
            if len(points) > 1:
                pygame.draw.lines(surface, (30, 40, 55), False, points, 1)
        
        # Court lines
        line_color = (60, 80, 100, 150)
        for x in range(0, 1281, 40):
            line_surf = pygame.Surface((30, 3), pygame.SRCALPHA)
            line_surf.fill(line_color)
            surface.blit(line_surf, (x, 357))
        
        pygame.draw.line(surface, (50, 70, 90), (100, 250), (1180, 250), 2)
        pygame.draw.line(surface, (50, 70, 90), (100, 470), (1180, 470), 2)
        pygame.draw.line(surface, (50, 70, 90), (100, 100), (100, 620), 2)
        pygame.draw.line(surface, (50, 70, 90), (1180, 100), (1180, 620), 2)
        
        # Powerups
        self._draw_powerups(surface)
        
        # Screen shake
        shake_x = random.randint(-int(self.screen_shake * 10), int(self.screen_shake * 10)) if self.screen_shake > 0 else 0
        shake_y = random.randint(-int(self.screen_shake * 10), int(self.screen_shake * 10)) if self.screen_shake > 0 else 0
        
        # Paddles
        self._draw_paddles(surface, shake_x, shake_y)
        
        # Ball
        self._draw_ball(surface, shake_x, shake_y)
        
        # Particles
        for p in self.particles:
            alpha = int(255 * (p['lifetime'] / p['max_lifetime']))
            color = p['color'] + (alpha,)
            particle_surf = pygame.Surface((p['size'] * 2, p['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, color, (p['size'], p['size']), p['size'])
            surface.blit(particle_surf, (int(p['x'] - p['size']), int(p['y'] - p['size'])))
        
        # HUD
        self._draw_hud(surface)
        
        # Floating texts
        for txt in self.floating_texts:
            alpha = int(255 * (txt['lifetime'] / txt['max_lifetime']))
            font = pygame.font.Font(None, txt['size'])
            text_surf = font.render(txt['text'], True, txt['color'])
            text_surf.set_alpha(alpha)
            surface.blit(text_surf, (int(txt['x'] - text_surf.get_width() // 2), int(txt['y'])))
        
        # Flash
        if self.flash_timer > 0:
            flash_alpha = int(min(180, self.flash_timer * 150))
            flash_surf = pygame.Surface((1280, 720), pygame.SRCALPHA)
            flash_surf.fill((255, 255, 255, flash_alpha))
            surface.blit(flash_surf, (0, 0))
        
        # Pause menu
        if self.paused and self.confirm_exit:
            overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))
            
            font_huge = pygame.font.Font(None, 100)
            pause_surf = font_huge.render("PAUSED", True, (255, 255, 255))
            surface.blit(pause_surf, (640 - pause_surf.get_width() // 2, 200))
            
            font_medium = pygame.font.Font(None, 48)
            exit_text = font_medium.render("LEFT CLICK = Exit", True, (255, 100, 100))
            continue_text = font_medium.render("RIGHT CLICK = Continue", True, (100, 255, 100))
            surface.blit(exit_text, (640 - exit_text.get_width() // 2, 350))
            surface.blit(continue_text, (640 - continue_text.get_width() // 2, 420))
        
        # Game Over
        if self.game_over:
            self._draw_game_over(surface)
    
    def _draw_powerups(self, surface: pygame.Surface):
        """Disegna powerup con grafica migliorata - BUG FIXED"""
        for pu in self.powerups_available:
            x, y = int(pu['x']), int(pu['y'])
            pulse_size = int(25 + abs(math.sin(pu['pulse'])) * 8)
            rotation = pu['rotation']
            
            # Outer glow
            glow_surf = pygame.Surface((pulse_size * 3, pulse_size * 3), pygame.SRCALPHA)
            for i in range(3):
                alpha = 60 - (i * 15)
                radius = pulse_size + (i * 8)
                pygame.draw.circle(glow_surf, pu['color'] + (alpha,), 
                                 (pulse_size * 3 // 2, pulse_size * 3 // 2), radius)
            surface.blit(glow_surf, (x - pulse_size * 3 // 2, y - pulse_size * 3 // 2))
            
            # Shape based on type
            shape = pu.get('shape', 'circle')
            
            if shape == 'rectangle':
                rect_surf = pygame.Surface((50, 50), pygame.SRCALPHA)
                pygame.draw.rect(rect_surf, pu['color'], (10, 15, 30, 8), 0, 3)
                pygame.draw.rect(rect_surf, (255, 255, 255), (10, 15, 30, 8), 2, 3)
                pygame.draw.rect(rect_surf, pu['color'], (10, 27, 30, 8), 0, 3)
                pygame.draw.rect(rect_surf, (255, 255, 255), (10, 27, 30, 8), 2, 3)
                rotated = pygame.transform.rotate(rect_surf, rotation)
                surface.blit(rotated, (x - rotated.get_width() // 2, y - rotated.get_height() // 2))
            
            elif shape == 'hourglass':
                pygame.draw.polygon(surface, pu['color'], [
                    (x - 12, y - 15), (x + 12, y - 15),
                    (x - 4, y), (x + 4, y),
                    (x - 12, y + 15), (x + 12, y + 15)
                ])
                pygame.draw.polygon(surface, (255, 255, 255), [
                    (x - 12, y - 15), (x + 12, y - 15),
                    (x - 4, y), (x + 4, y),
                    (x - 12, y + 15), (x + 12, y + 15)
                ], 2)
            
            elif shape == 'triple_circle':
                # BUG FIXED: offset è una tupla (x_offset, y_offset)
                offsets = [(-10, -8), (10, -8), (0, 8)]
                for x_offset, y_offset in offsets:
                    pygame.draw.circle(surface, pu['color'], (x + x_offset, y + y_offset), 7)
                    pygame.draw.circle(surface, (255, 255, 255), (x + x_offset, y + y_offset), 7, 2)
            
            elif shape == 'shield':
                points = [
                    (x, y - 16),
                    (x - 14, y - 8),
                    (x - 14, y + 8),
                    (x, y + 16),
                    (x + 14, y + 8),
                    (x + 14, y - 8)
                ]
                pygame.draw.polygon(surface, pu['color'], points)
                pygame.draw.polygon(surface, (255, 255, 255), points, 3)
                pygame.draw.line(surface, (255, 255, 255), (x - 8, y), (x + 8, y), 2)
                pygame.draw.line(surface, (255, 255, 255), (x, y - 10), (x, y + 10), 2)
            
            elif shape == 'lightning':
                lightning = [
                    (x - 5, y - 15),
                    (x + 5, y - 5),
                    (x - 2, y),
                    (x + 8, y + 15),
                    (x - 3, y + 5),
                    (x + 2, y)
                ]
                pygame.draw.polygon(surface, (255, 255, 100), lightning)
                pygame.draw.polygon(surface, (255, 255, 255), lightning, 2)
            
            # Central highlight
            pygame.draw.circle(surface, (255, 255, 255, 200), (x, y), 3)
    





    def _draw_paddles(self, surface: pygame.Surface, shake_x: int, shake_y: int):
        """Disegna paddle con effetti - SIMMETRICO"""
        
        # DISTANZA UGUALE DAI BORDI: 30px
        EDGE_DISTANCE = 30
        
        # Bottom paddle (player) - 30px dal bordo inferiore
        paddle_y_bottom = 720 - EDGE_DISTANCE - self.paddle_height  # 720 - 30 - 15 = 675
        
        glow_surf_bottom = pygame.Surface((self.paddle_width + 12, self.paddle_height + 8), pygame.SRCALPHA)
        glow_surf_bottom.fill((100, 255, 150, 60))
        surface.blit(glow_surf_bottom, 
                    (int(self.paddle_bottom_x - (self.paddle_width + 12) // 2) + shake_x, 
                    paddle_y_bottom - 4 + shake_y))
        
        pygame.draw.rect(surface, (100, 255, 150), 
                        (int(self.paddle_bottom_x - self.paddle_width // 2) + shake_x, 
                        paddle_y_bottom + shake_y, 
                        self.paddle_width, self.paddle_height), 0, 5)
        pygame.draw.rect(surface, (180, 255, 200), 
                        (int(self.paddle_bottom_x - self.paddle_width // 2) + shake_x, 
                        paddle_y_bottom + shake_y, 
                        self.paddle_width, self.paddle_height), 3, 5)
        
        # Top paddle (AI) - 30px dal bordo superiore
        paddle_y_top = EDGE_DISTANCE  # 30px dal top
        
        glow_surf_top = pygame.Surface((self.paddle_width + 12, self.paddle_height + 8), pygame.SRCALPHA)
        glow_surf_top.fill((255, 120, 120, 60))
        surface.blit(glow_surf_top, 
                    (int(self.paddle_top_x - (self.paddle_width + 12) // 2) + shake_x, 
                    paddle_y_top - 4 + shake_y))
        
        pygame.draw.rect(surface, (255, 120, 120), 
                        (int(self.paddle_top_x - self.paddle_width // 2) + shake_x, 
                        paddle_y_top + shake_y, 
                        self.paddle_width, self.paddle_height), 0, 5)
        pygame.draw.rect(surface, (255, 180, 180), 
                        (int(self.paddle_top_x - self.paddle_width // 2) + shake_x, 
                        paddle_y_top + shake_y, 
                        self.paddle_width, self.paddle_height), 3, 5)




    def _draw_ball(self, surface: pygame.Surface, shake_x: int, shake_y: int):
        """Disegna palla con trail"""
        # Trail
        for i, (tx, ty) in enumerate(self.ball_trail):
            if len(self.ball_trail) > 0:
                alpha = int((i / len(self.ball_trail)) * 200)
                size = int(2 + (i / len(self.ball_trail)) * 4)
                trail_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(trail_surf, (255, 255, 200, alpha), (size, size), size)
                surface.blit(trail_surf, (int(tx - size) + shake_x, int(ty - size) + shake_y))
        
        # Glow
        glow_size = int(self.ball_size + 8 + abs(math.sin(self.ball_glow_pulse)) * 4)
        ball_glow = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(ball_glow, (255, 255, 150, 120), (glow_size, glow_size), glow_size)
        surface.blit(ball_glow, (int(self.ball_x - glow_size) + shake_x, 
                                int(self.ball_y - glow_size) + shake_y))
        
        # Ball core
        pygame.draw.circle(surface, (255, 255, 220), 
                          (int(self.ball_x) + shake_x, int(self.ball_y) + shake_y), 
                          self.ball_size)
        pygame.draw.circle(surface, (255, 255, 255), 
                          (int(self.ball_x) + shake_x, int(self.ball_y) + shake_y), 
                          self.ball_size - 2)
            
    def _draw_hud(self, surface: pygame.Surface):
        """HUD elegante minimalista - LAYOUT SIMMETRICO"""
        font_score = pygame.font.Font(None, 64)
        font_label = pygame.font.Font(None, 22)
        font_small = pygame.font.Font(None, 20)
        font_tiny = pygame.font.Font(None, 18)
        
        # === PLAYER SCORE (Bottom Left) ===
        player_panel_width = 90
        player_panel_height = 70
        player_panel_x = 30
        player_panel_y = 640
        
        player_bg = pygame.Surface((player_panel_width, player_panel_height), pygame.SRCALPHA)
        player_bg.fill((0, 0, 0, 110))
        surface.blit(player_bg, (player_panel_x, player_panel_y))
        
        player_label = font_label.render("YOU", True, (150, 220, 180))
        player_label.set_alpha(210)
        label_x = player_panel_x + (player_panel_width - player_label.get_width()) // 2
        surface.blit(player_label, (label_x, player_panel_y + 5))
        
        player_score_text = font_score.render(str(self.score_player), True, (120, 255, 170))
        player_score_text.set_alpha(240)
        score_x = player_panel_x + (player_panel_width - player_score_text.get_width()) // 2
        surface.blit(player_score_text, (score_x, player_panel_y + 30))
        
        # === AI SCORE (Top Left) - SIMMETRICO ===
        ai_panel_width = 90
        ai_panel_height = 70
        ai_panel_x = 30
        ai_panel_y = 10
        
        ai_bg = pygame.Surface((ai_panel_width, ai_panel_height), pygame.SRCALPHA)
        ai_bg.fill((0, 0, 0, 110))
        surface.blit(ai_bg, (ai_panel_x, ai_panel_y))
        
        ai_label = font_label.render("CPU", True, (220, 150, 150))
        ai_label.set_alpha(210)
        ai_label_x = ai_panel_x + (ai_panel_width - ai_label.get_width()) // 2
        surface.blit(ai_label, (ai_label_x, ai_panel_y + 5))
        
        ai_score_text = font_score.render(str(self.score_ai), True, (255, 140, 140))
        ai_score_text.set_alpha(240)
        ai_score_x = ai_panel_x + (ai_panel_width - ai_score_text.get_width()) // 2
        surface.blit(ai_score_text, (ai_score_x, ai_panel_y + 30))
        
        # === TOTAL SCORE (Top Right) ===
        total_score_panel_width = 180
        total_score_panel_height = 35
        total_score_panel_x = 1070
        total_score_panel_y = 10
        
        total_score_panel = pygame.Surface((total_score_panel_width, total_score_panel_height), pygame.SRCALPHA)
        total_score_panel.fill((0, 0, 0, 115))
        surface.blit(total_score_panel, (total_score_panel_x, total_score_panel_y))
        
        total_score_text = font_small.render(f"SCORE: {self.score}", True, (200, 220, 255))
        total_score_text.set_alpha(230)
        total_x = total_score_panel_x + (total_score_panel_width - total_score_text.get_width()) // 2
        surface.blit(total_score_text, (total_x, total_score_panel_y + 10))
        
        # === RALLY COUNTER (Bottom Right) ===
        if self.rally_count >= 3 and not self.game_over and not self.paused:
            rally_panel_width = 140
            rally_panel_height = 40
            rally_panel_x = 1110
            rally_panel_y = 665
            
            rally_bg = pygame.Surface((rally_panel_width, rally_panel_height), pygame.SRCALPHA)
            rally_bg.fill((0, 0, 0, 130))
            surface.blit(rally_bg, (rally_panel_x, rally_panel_y))
            
            rally_color = (255, 255, 120) if self.rally_count < 10 else (255, 150, 255)
            font_rally = pygame.font.Font(None, 34)
            rally_text = font_rally.render(f"RALLY x{self.rally_count}", True, rally_color)
            rally_text.set_alpha(245)
            text_x = rally_panel_x + (rally_panel_width - rally_text.get_width()) // 2
            surface.blit(rally_text, (text_x, rally_panel_y + 8))
        
        # === COMBO MULTIPLIER (Center - Solo se attivo) ===
        if self.combo_multiplier > 1.0 and not self.game_over and not self.paused:
            combo_panel_width = 100
            combo_panel_height = 32
            combo_panel_x = 640 - combo_panel_width // 2
            combo_panel_y = 345
            
            combo_bg = pygame.Surface((combo_panel_width, combo_panel_height), pygame.SRCALPHA)
            combo_bg.fill((0, 0, 0, 115))
            surface.blit(combo_bg, (combo_panel_x, combo_panel_y))
            
            combo_text = font_small.render(f"x{self.combo_multiplier:.1f}", True, (255, 220, 100))
            combo_text.set_alpha(220)
            combo_x = combo_panel_x + (combo_panel_width - combo_text.get_width()) // 2
            surface.blit(combo_text, (combo_x, combo_panel_y + 8))
        
        # === ACTIVE POWERUP (Top Right - Sotto Total Score) ===
        if self.active_powerup:
            pu_colors = {
                'big_paddle': (100, 200, 255),
                'slow_ball': (150, 255, 150),
                'multi_ball': (255, 200, 100),
                'shield': (255, 150, 255),
                'speed_boost': (255, 255, 100)
            }
            pu_names = {
                'big_paddle': 'BIG PADDLE',
                'slow_ball': 'SLOW BALL',
                'multi_ball': 'MULTI BALL',
                'shield': 'SHIELD',
                'speed_boost': 'SPEED UP'
            }
            
            pu_color = pu_colors.get(self.active_powerup, (255, 255, 255))
            pu_name = pu_names.get(self.active_powerup, 'POWERUP')
            
            pu_panel_width = 150
            pu_panel_height = 45
            pu_panel_x = 1085
            pu_panel_y = 55
            
            pu_bg = pygame.Surface((pu_panel_width, pu_panel_height), pygame.SRCALPHA)
            pu_bg.fill((0, 0, 0, 120))
            surface.blit(pu_bg, (pu_panel_x, pu_panel_y))
            
            pu_text = font_tiny.render(pu_name, True, pu_color)
            pu_text.set_alpha(235)
            text_x = pu_panel_x + (pu_panel_width - pu_text.get_width()) // 2
            surface.blit(pu_text, (text_x, pu_panel_y + 5))
            
            bar_width = 130
            bar_height = 5
            bar_x = pu_panel_x + (pu_panel_width - bar_width) // 2
            bar_y = pu_panel_y + 30
            
            pygame.draw.rect(surface, (40, 40, 40, 180), (bar_x, bar_y, bar_width, bar_height), 0, 2)
            
            timer_fill = int(bar_width * (self.powerup_timer / self.powerup_duration))
            if timer_fill > 0:
                timer_surf = pygame.Surface((timer_fill, bar_height), pygame.SRCALPHA)
                timer_surf.fill(pu_color + (210,))
                surface.blit(timer_surf, (bar_x, bar_y))
            
            pygame.draw.rect(surface, pu_color + (200,), (bar_x, bar_y, bar_width, bar_height), 1, 2)


    def _draw_game_over(self, surface: pygame.Surface):
        """Game Over screen"""
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        
        font_huge = pygame.font.Font(None, 110)
        font_large = pygame.font.Font(None, 56)
        font_medium = pygame.font.Font(None, 40)
        font_small = pygame.font.Font(None, 32)
        
        if self.score_player >= self.max_score:
            result_text, result_color = "VICTORY!", (120, 255, 170)
        else:
            result_text, result_color = "DEFEAT", (255, 140, 140)
        
        shadow = font_huge.render(result_text, True, (0, 0, 0))
        surface.blit(shadow, (642 - shadow.get_width() // 2, 82))
        
        result = font_huge.render(result_text, True, result_color)
        surface.blit(result, (640 - result.get_width() // 2, 80))
        
        final_score = font_large.render(f"FINAL SCORE: {self.score}", True, (255, 255, 255))
        surface.blit(final_score, (640 - final_score.get_width() // 2, 220))
        
        match_result = font_medium.render(f"{self.score_player} - {self.score_ai}", True, (220, 220, 220))
        surface.blit(match_result, (640 - match_result.get_width() // 2, 290))
        
        stats_y = 360
        stats = [
            f"Max Rally: {self.max_rally}",
            f"Total Hits: {self.total_hits}",
            f"Perfect Hits: {self.perfect_hits}",
            f"Powerups Used: {self.powerups_collected}",
            f"Duration: {int(self.match_duration)}s"
        ]
        
        for stat in stats:
            stat_surf = font_small.render(stat, True, (200, 210, 230))
            surface.blit(stat_surf, (640 - stat_surf.get_width() // 2, stats_y))
            stats_y += 40
        
        hint = font_medium.render("RIGHT CLICK to continue", True, (150, 170, 180))
        surface.blit(hint, (640 - hint.get_width() // 2, 640))















class MissileCommander(MiniGame):

    def __init__(self, synth):
        super().__init__()
        self.last_powerup_spawn_time = 0
        self.synth = synth
        self.paused = False
        self.confirm_exit = False
        self.reset()

    def get_name(self) -> str:
        return "Missile Commander"

    def get_description(self) -> str:
        return "Defend cities! Hold 4s for NUKE!"

    def reset(self):
        self.score = 0
        self.game_over = False
        self.wave = 1
        self.time = 0
        self.paused = False
        self.confirm_exit = False

        self.tank_x = 640
        self.tank_y = 680
        self.tank_angle = -90
        self.tank_tracks_offset = 0

        self.health = 5
        self.max_health = 5
        self.combo = 0
        self.combo_timer = 0
        self.combo_decay_time = 3.5
        self.combo_multiplier = 1.0
        self.max_combo = 0

        # SISTEMA NUKE PERFETTO - 4 SECONDI
        self.charge_time = 0
        self.max_charge_time = 4.0
        self.min_charge_display = 1.0
        self.was_pressing = False
        self.shot_cooldown = 0
        self.shot_interval = 0.15
        self.first_shot_fired = False

        self.total_shots = 0
        self.total_hits = 0
        self.accuracy = 0

        self.active_powerup = None
        self.powerup_ammo = 0

        self.missiles = []
        self.explosions = []
        self.bullets = []
        self.powerups = []
        self.particles = []
        self.cities = []
        self.floating_texts = []

        self.spawn_timer = 0
        self.spawn_interval = 3.0
        self.missiles_destroyed_this_wave = 0
        self.missiles_needed_for_wave = 8

        self.screen_flash = 0
        self.background_color = (5, 5, 30)
        self.stars = []
        for _ in range(150):
            self.stars.append({
                'x': random.randint(0, 1280),
                'y': random.randint(0, 600),
                'brightness': random.randint(80, 255),
                'size': random.randint(1, 3),
                'speed': random.uniform(0.2, 1.5),
                'twinkle': random.uniform(0, math.pi * 2)
            })

        self.meteors = []

        city_positions = [150, 320, 490, 790, 960, 1130]
        city_types = ['apartment', 'office', 'house', 'skyscraper', 'factory', 'tower']
        for i, x in enumerate(city_positions):
            self.cities.append({
                'x': x,
                'y': 660,
                'alive': True,
                'type': city_types[i % len(city_types)],
                'width': random.randint(50, 70),
                'height': random.randint(40, 60),
                'windows': self.generate_windows(),
                'destroyed_time': 0
            })

    def generate_windows(self):
        windows = []
        for row in range(3):
            for col in range(3):
                if random.random() > 0.2:
                    windows.append({
                        'x': col * 15 + 5,
                        'y': row * 12 + 5,
                        'lit': random.random() > 0.3
                    })
        return windows




    def spawn_missile(self):
        """Spawna un nuovo missile nemico con logica di progressione avanzata e densità scalare per wave."""

        # 0. LIMITATORE DI DENSITÀ IN BASE ALLA WAVE
        # Aumenta più aggressivo:
        # wave 1 -> ~6, wave 5 -> ~12, wave 10 -> ~20 (clamp a 24)
        max_concurrent = min(6 + int(self.wave * 1.5), 24)
        if len(self.missiles) >= max_concurrent:
            return

        # 0bis. MULTISPAWN PER WAVE ALTA
        # Alle prime wave 1 missile alla volta, poi 2, poi 3
        if self.wave < 4:
            spawn_count = 1
        elif self.wave < 8:
            spawn_count = 2
        else:
            spawn_count = 3

        for _ in range(spawn_count):
            # Se durante il loop raggiungi il limite, fermati
            if len(self.missiles) >= max_concurrent:
                break

            # 1. SELEZIONE TIPO (Progressione scalare)
            if self.wave < 3:
                weights = {'standard': 100, 'fast': 0, 'heavy': 0, 'jitter': 0}
            elif self.wave < 5:
                weights = {'standard': 70, 'fast': 30, 'heavy': 0, 'jitter': 0}
            elif self.wave < 7:
                weights = {'standard': 50, 'fast': 30, 'heavy': 20, 'jitter': 0}
            else:
                # Endgame mix
                weights = {'standard': 40, 'fast': 25, 'heavy': 20, 'jitter': 15}
                
            types = list(weights.keys())
            probs = list(weights.values())
            m_type = random.choices(types, weights=probs, k=1)[0]
            
            # 2. CONFIGURAZIONE STATS PER TIPO
            level_speed_mult = 1.0 + (self.wave * 0.1)
            base_speed = 60
            size = 14
            
            if m_type == 'standard':
                speed_val = base_speed * 1.0
                size = 14
            elif m_type == 'fast':
                speed_val = base_speed * 1.8
                size = 10
            elif m_type == 'heavy':
                speed_val = base_speed * 0.7
                size = 20
            elif m_type == 'jitter':
                speed_val = base_speed * 1.3
                size = 12
                
            final_speed = speed_val * level_speed_mult * random.uniform(0.9, 1.1)

            # 3. POSIZIONAMENTO INTELLIGENTE
            start_x = random.randint(50, 1230)
            start_y = -20
            
            alive_cities = [c for c in self.cities if c['alive']]
            target_city = None
            if alive_cities:
                aim_prob = 0.6
                if m_type == 'heavy':
                    aim_prob = 0.9
                if m_type == 'jitter':
                    aim_prob = 0.3
                
                if random.random() < aim_prob:
                    target_city = random.choice(alive_cities)
                    scatter = 30 if m_type != 'heavy' else 10
                    target_x = target_city['x'] + random.randint(-scatter, scatter)
                else:
                    target_x = random.randint(100, 1180)
            else:
                target_x = random.randint(100, 1180)

            target_y = 660
            
            dx = target_x - start_x
            dy = target_y - start_y
            dist = math.sqrt(dx**2 + dy**2)
            if dist == 0:
                dist = 1
            
            vx = (dx / dist) * final_speed
            vy = (dy / dist) * final_speed

            missile = {
                'x': start_x,
                'y': start_y,
                'vx': vx,
                'vy': vy,
                'target_x': target_x,
                'target_y': target_y,
                'alive': True,
                'trail': [],
                'type': m_type,
                'size': size,
                'has_split': False
            }
            
            if m_type == 'jitter':
                missile['jitter_phase'] = random.uniform(0, math.pi * 2)
                
            self.missiles.append(missile)





    def spawn_powerup(self, x: float, y: float):
        """
        Sistema di spawn powerup con cooldown, rarità bilanciate e limite su schermo.
        Richiede: self.last_powerup_spawn_time (inizializza nel __init__ a 0)
        """
        current_time = pygame.time.get_ticks()
        
        # COOLDOWN GLOBALE: minimo 2 secondi tra uno spawn e l'altro
        if current_time - getattr(self, 'last_powerup_spawn_time', 0) < 2000:
            return
        
        # CONTROLLO SATURAZIONE: max 2 powerup attivi contemporaneamente
        if len(self.powerups) >= 2:
            return
        
        # Probabilità base ultra-ridotta: 18% invece di 65%
        if random.random() < 0.18:
            # Weighted Random Choice: life diventa rarissimo
            powerup_pool = ['shotgun', 'laser', 'grenade', 'life']
            weights = [35, 40, 30, 5]  # life 6-7x più raro
            
            ptype = random.choices(powerup_pool, weights=weights, k=1)[0]
            
            colors = {
                'shotgun': (255, 220, 80),
                'laser': (0, 255, 255),
                'grenade': (255, 100, 0),
                'life': (0, 255, 120)
            }

            self.powerups.append({
                'x': x,
                'y': y,
                'type': ptype,
                'color': colors[ptype],
                'vy': 100,
                'alive': True,
                'pulse': 0,
                'rotation': 0
            })
            
            self.last_powerup_spawn_time = current_time




    def create_explosion(self, x: float, y: float, radius: float, color: Tuple[int, int, int]):
        self.explosions.append({
            'x': x,
            'y': y,
            'radius': 5,
            'max_radius': radius,
            'lifetime': 1.0,
            'max_lifetime': 1.0,
            'color': color
        })

        particle_count = int(radius / 2.5)
        for _ in range(particle_count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(80, 250)
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed - random.uniform(0, 50),
                'lifetime': random.uniform(0.4, 1.2),
                'max_lifetime': 1.2,
                'color': color,
                'size': random.uniform(2, 6),
                'fade': random.choice([True, False])
            })







    def add_floating_text(self, x: float, y: float, text: str, color: Tuple[int, int, int], size: int = 36):
        self.floating_texts.append({
            'x': x,
            'y': y,
            'text': text,
            'color': color,
            'lifetime': 1.5,
            'max_lifetime': 1.5,
            'vy': -80,
            'size': size
        })



























    def fire_weapon(self, charge_level: float):
        """Ottimizzato: calcoli preliminari unificati e grafica migliorata"""
        self.total_shots += 1
        
        # Calcoli comuni una sola volta
        rad = math.radians(self.tank_angle)
        cos_rad, sin_rad = math.cos(rad), math.sin(rad)
        barrel_length = 55
        start_x = self.tank_x + cos_rad * barrel_length
        start_y = self.tank_y + sin_rad * barrel_length - 10
        
        # Muzzle flash migliorato con più particelle
        self._create_muzzle_flash(start_x, start_y, rad)
        
        # SUPER GRENADE (Nuke)
        if charge_level >= 1.0:
            self._fire_super_grenade(start_x, start_y, cos_rad, sin_rad)
            return
        
        # POWERUP WEAPONS
        if self.active_powerup and self.powerup_ammo > 0:
            self.powerup_ammo -= 1
            
            if self.active_powerup == 'shotgun':
                self._fire_shotgun(start_x, start_y, rad)  # <--- PASSA rad (già in radianti)
            elif self.active_powerup == 'laser':
                self._fire_laser(start_x, start_y, cos_rad, sin_rad)
            elif self.active_powerup == 'grenade':
                self._fire_grenade(start_x, start_y, cos_rad, sin_rad)
            
            if self.powerup_ammo == 0:
                self.active_powerup = None
            
            self.synth.create_hit().play()
            return
        
        # NORMAL BULLET
        self._fire_normal_bullet(start_x, start_y, cos_rad, sin_rad)
        self.synth.create_hit().play()

    def _fire_shotgun(self, x: float, y: float, base_angle_rad: float):  # <--- Parametro rinominato
        """Shotgun con spread pattern migliorato"""
        spread_count = 9
        spread_angle = 6  # gradi
        
        for i in range(spread_count):
            spread_deg = (i - spread_count // 2) * spread_angle
            angle_rad = base_angle_rad + math.radians(spread_deg)  # <--- Converti SOLO lo spread
            
            # Velocità variabile per pattern più naturale
            speed_variation = random.uniform(0.95, 1.05)
            speed = 750 * speed_variation
            
            self.bullets.append({
                'x': x, 'y': y,
                'vx': math.cos(angle_rad) * speed,
                'vy': math.sin(angle_rad) * speed,
                'type': 'shotgun',
                'alive': True,
                'color': (255, 220, 80),
                'trail': [],
                'size': 8,
                'lifetime': 0
            })

    def _create_muzzle_flash(self, x: float, y: float, angle: float):
        """Muzzle flash migliorato con particelle multiple"""
        # Flash centrale più grande
        self.create_explosion(x, y, 30, (255, 255, 200))
        
        # Particelle direzionali
        for i in range(5):
            offset_angle = angle + math.radians(random.uniform(-15, 15))
            dist = random.uniform(10, 25)
            px = x + math.cos(offset_angle) * dist
            py = y + math.sin(offset_angle) * dist
            self.create_explosion(px, py, 12, (255, 200, 100))

    def _fire_super_grenade(self, x: float, y: float, cos_rad: float, sin_rad: float):
        """Nuke con effetti grafici migliorati"""
        self.bullets.append({
            'x': x, 'y': y,
            'vx': cos_rad * 450,
            'vy': sin_rad * 450,
            'type': 'super_grenade',
            'alive': True,
            'color': (255, 50, 255),
            'trail': [],
            'glow': 0,
            'size': 15,
            'pulse': 0  # Per effetto pulsante
        })
        
        # Effetti aggiuntivi
        self.synth.create_hit().play()
        self.add_floating_text(640, 350, "⚛ NUKE LAUNCHED! ⚛", (255, 50, 255), 56)
        
        # Particelle extra per l'effetto drammatico
        for i in range(8):
            angle = (i / 8) * math.pi * 2
            self.create_explosion(
                x + math.cos(angle) * 30,
                y + math.sin(angle) * 30,
                15, (255, 100, 255)
            )


    def _fire_laser(self, x: float, y: float, cos_rad: float, sin_rad: float):
        """Laser con beam width pulsante"""
        laser_length = 2000
        end_x = x + cos_rad * laser_length
        end_y = y + sin_rad * laser_length
        
        self.bullets.append({
            'x1': x,
            'y1': y - 10,
            'x2': end_x,
            'y2': end_y,
            'type': 'laser',
            'lifetime': 0.35,  # Leggermente più lungo
            'alive': True,
            'hit_missiles': set(),
            'beam_width': 12,  # Aumentato
            'intensity': 1.0,  # Per fade-out
            'color': (100, 200, 255)
        })
        
        # Impatto visivo al punto di origine
        self.create_explosion(x, y - 10, 20, (150, 220, 255))

    def _fire_grenade(self, x: float, y: float, cos_rad: float, sin_rad: float):
        """Granata con rotazione e trail migliorati"""
        self.bullets.append({
            'x': x, 'y': y,
            'vx': cos_rad * 550,
            'vy': sin_rad * 550,
            'type': 'grenade',
            'alive': True,
            'color': (255, 120, 0),
            'trail': [],
            'rotation': 0,
            'rotation_speed': random.uniform(8, 12),  # Velocità rotazione casuale
            'size': 10,
            'spark_timer': 0  # Per scintille periodiche
        })

    def _fire_normal_bullet(self, x: float, y: float, cos_rad: float, sin_rad: float):
        """Proiettile normale con trail migliorato"""
        self.bullets.append({
            'x': x, 'y': y,
            'vx': cos_rad * 850,
            'vy': sin_rad * 850,
            'type': 'normal',
            'alive': True,
            'color': (255, 255, 120),
            'trail': [],
            'size': 9,
            'glow_intensity': 1.0  # Per glow pulsante
        })













    def line_circle_collision(self, x1, y1, x2, y2, cx, cy, radius):
        dx = cx - x1
        dy = cy - y1
        lx = x2 - x1
        ly = y2 - y1
        len_sq = lx * lx + ly * ly

        if len_sq == 0:
            return False

        t = max(0, min(1, (dx * lx + dy * ly) / len_sq))
        closest_x = x1 + t * lx
        closest_y = y1 + t * ly
        dist_sq = (cx - closest_x) ** 2 + (cy - closest_y) ** 2

        return dist_sq <= radius * radius






    def update_combo(self, dt: float, missile_destroyed: bool = False):
        if missile_destroyed:
            self.combo += 1
            self.combo_timer = self.combo_decay_time
            self.combo_multiplier = 1.0 + (self.combo * 0.15)
            self.max_combo = max(self.max_combo, self.combo)

            if self.combo >= 3:
                combo_colors = {
                    3: (255, 255, 100),
                    5: (255, 200, 100),
                    10: (255, 150, 50),
                    15: (255, 100, 255),
                    20: (255, 50, 50)
                }
                color = combo_colors.get(self.combo, (255, 255, 255))
                if self.combo in combo_colors:
                    text = f"COMBO x{self.combo}!"
                    self.add_floating_text(640, 300, text, color, 48)
        else:
            if self.combo > 0:
                self.combo_timer -= dt
                if self.combo_timer <= 0:
                    if self.combo >= 5:
                        self.add_floating_text(640, 350, f"Combo Lost! (x{self.combo})", 
                                             (255, 100, 100), 40)
                    self.combo = 0
                    self.combo_multiplier = 1.0






    def update(self, dt: float, spinner_delta: float, spinner) -> bool:
        if spinner.is_right_clicked():
            if not self.paused:
                self.paused = True
                self.confirm_exit = True
            elif self.confirm_exit:
                self.paused = False
                self.confirm_exit = False

        if self.paused and self.confirm_exit:
            if spinner.is_left_clicked():
                return False
            return True

        if self.game_over:
            # Continua ad aggiornare animazioni anche quando game over
            self.time += dt
            # Non intercettare input - lascia che PlayingState gestisca high scores
            return True
        self.time += dt

        wave_colors = [
            (5, 5, 30),
            (10, 5, 40),
            (30, 10, 10),
            (5, 20, 40),
            (40, 20, 5),
        ]
        target_color = wave_colors[min(self.wave - 1, len(wave_colors) - 1)]
        self.background_color = tuple(
            int(self.background_color[i] + (target_color[i] - self.background_color[i]) * dt * 0.5)
            for i in range(3)
        )

        self.tank_angle += spinner_delta * 0.35
        self.tank_angle = max(-160, min(-20, self.tank_angle))

        if abs(spinner_delta) > 0.1:
            self.tank_tracks_offset += dt * spinner_delta * 2
            if self.tank_tracks_offset > 10:
                self.tank_tracks_offset = 0
            elif self.tank_tracks_offset < -10:
                self.tank_tracks_offset = 0

        # ===== SISTEMA NUKE PERFETTO =====
        is_pressing = spinner.is_left_pressed()

        if self.shot_cooldown > 0:
            self.shot_cooldown -= dt

        if is_pressing:
            if not self.was_pressing:
                if self.shot_cooldown <= 0:
                    self.fire_weapon(0.0)
                    self.shot_cooldown = self.shot_interval
                    self.first_shot_fired = True
                    self.charge_time = 0
            
            if self.first_shot_fired:
                if self.charge_time < self.max_charge_time:
                    self.charge_time += dt
                    if self.charge_time > self.max_charge_time:
                        self.charge_time = self.max_charge_time
        else:
            if self.was_pressing and self.first_shot_fired:
                if self.charge_time >= self.max_charge_time:
                    self.fire_weapon(1.0)
                    self.shot_cooldown = 0.5
                self.charge_time = 0
                self.first_shot_fired = False

        self.was_pressing = is_pressing
        # ===== FINE SISTEMA NUKE =====

        if self.screen_flash > 0:
            self.screen_flash -= dt * 3

        self.update_combo(dt, False)

        for star in self.stars:
            star['twinkle'] += dt * 3
            star['x'] -= star['speed'] * dt * 5
            if star['x'] < -10:
                star['x'] = 1290
                star['y'] = random.randint(0, 600)

        if random.random() < dt * 0.3:
            self.meteors.append({
                'x': random.randint(0, 1280),
                'y': 0,
                'vx': random.uniform(-100, 100),
                'vy': random.uniform(200, 400),
                'lifetime': 2.0,
                'trail': []
            })

        for meteor in self.meteors[:]:
            meteor['x'] += meteor['vx'] * dt
            meteor['y'] += meteor['vy'] * dt
            meteor['lifetime'] -= dt
            meteor['trail'].append((meteor['x'], meteor['y']))
            if len(meteor['trail']) > 15:
                meteor['trail'].pop(0)
            if meteor['lifetime'] <= 0 or meteor['y'] > 720:
                self.meteors.remove(meteor)

        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_missile()
            self.spawn_timer = 0
            self.spawn_interval = max(0.8, 3.0 - self.wave * 0.15)

        for exp in self.explosions[:]:
            exp['lifetime'] -= dt
            progress = 1 - (exp['lifetime'] / exp['max_lifetime'])
            exp['radius'] = exp['max_radius'] * min(1.0, progress * 2)
            if exp['lifetime'] <= 0:
                self.explosions.remove(exp)

        for p in self.particles[:]:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] += 250 * dt
            p['vx'] *= 0.98
            p['lifetime'] -= dt
            if p['lifetime'] <= 0:
                self.particles.remove(p)

        for txt in self.floating_texts[:]:
            txt['y'] += txt['vy'] * dt
            txt['lifetime'] -= dt
            if txt['lifetime'] <= 0:
                self.floating_texts.remove(txt)

        for missile in self.missiles[:]:
            missile['trail'].append((missile['x'], missile['y']))
            if len(missile['trail']) > 25:
                missile['trail'].pop(0)

            missile['x'] += missile['vx'] * dt
            missile['y'] += missile['vy'] * dt

            if missile['type'] == 'split' and not missile['has_split'] and missile['y'] > 300:
                missile['has_split'] = True
                for offset in [-50, 50]:
                    new_target_x = missile['target_x'] + offset
                    dx = new_target_x - missile['x']
                    dy = missile['target_y'] - missile['y']
                    dist = math.sqrt(dx**2 + dy**2)
                    speed = math.sqrt(missile['vx']**2 + missile['vy']**2)
                    self.missiles.append({
                        'x': missile['x'],
                        'y': missile['y'],
                        'vx': (dx / dist) * speed,
                        'vy': (dy / dist) * speed,
                        'target_x': new_target_x,
                        'target_y': missile['target_y'],
                        'alive': True,
                        'trail': [],
                        'type': 'normal',
                        'size': 12,
                        'has_split': True
                    })
                self.missiles.remove(missile)
                continue

            dist = math.sqrt((missile['x'] - missile['target_x'])**2 + 
                           (missile['y'] - missile['target_y'])**2)

            if dist < 10 or missile['y'] > 665:
                self.create_explosion(missile['x'], missile['y'], 90, (255, 80, 0))
                self.missiles.remove(missile)

                for city in self.cities:
                    if city['alive']:
                        city_dist = abs(missile['x'] - city['x'])
                        if city_dist < 50:
                            city['alive'] = False
                            city['destroyed_time'] = self.time
                            self.health -= 1
                            self.screen_flash = 1.2
                            self.combo = 0
                            self.combo_multiplier = 1.0
                            self.add_floating_text(city['x'], city['y'] - 50, 
                                                 "CITY LOST!", (255, 50, 50), 42)
                            self.synth.create_game_over().play()
                            if self.health <= 0:
                                self.game_over = True
                                if self.total_shots > 0:
                                    self.accuracy = int((self.total_hits / self.total_shots) * 100)
                            break

        for bullet in self.bullets[:]:
            if bullet['type'] == 'laser':
                bullet['lifetime'] -= dt
                bullet['beam_width'] = int(bullet.get('beam_width', 10) * (bullet['lifetime'] / 0.3))

                for missile in self.missiles[:]:
                    if id(missile) not in bullet['hit_missiles']:
                        if self.line_circle_collision(
                            bullet['x1'], bullet['y1'],
                            bullet['x2'], bullet['y2'],
                            missile['x'], missile['y'], missile['size']
                        ):
                            bullet['hit_missiles'].add(id(missile))
                            self.missiles.remove(missile)
                            self.create_explosion(missile['x'], missile['y'], 70, (0, 255, 255))
                            points = int(100 * self.combo_multiplier)
                            self.score += points
                            self.total_hits += 1
                            self.add_floating_text(missile['x'], missile['y'], 
                                                 f"+{points}", (0, 255, 255), 32)
                            self.spawn_powerup(missile['x'], missile['y'])
                            self.update_combo(dt, True)
                            self.synth.create_score_point().play()

                if bullet['lifetime'] <= 0:
                    self.bullets.remove(bullet)
                continue

            if 'trail' in bullet:
                bullet['trail'].append((bullet['x'], bullet['y']))
                if len(bullet['trail']) > 12:
                    bullet['trail'].pop(0)

            if 'rotation' in bullet:
                bullet['rotation'] += dt * 720

            if 'glow' in bullet:
                bullet['glow'] = (bullet['glow'] + dt * 10) % (math.pi * 2)

            bullet['x'] += bullet['vx'] * dt
            bullet['y'] += bullet['vy'] * dt

            if not (0 < bullet['x'] < 1280 and 0 < bullet['y'] < 720):
                if bullet in self.bullets:
                    self.bullets.remove(bullet)
                continue

            hit = False
            for missile in self.missiles[:]:
                bullet_size = bullet.get('size', 9)
                missile_size = missile.get('size', 14)
                collision_dist = bullet_size + missile_size

                dist = math.sqrt((bullet['x'] - missile['x'])**2 + 
                               (bullet['y'] - missile['y'])**2)

                if dist < collision_dist:
                    self.missiles.remove(missile)
                    points = int(100 * self.combo_multiplier)
                    self.score += points
                    self.total_hits += 1

                    if bullet['type'] == 'super_grenade':
                        self.create_explosion(bullet['x'], bullet['y'], 450, (255, 50, 255))
                        self.screen_flash = 2.0
                        self.add_floating_text(640, 250, "*** NUKE ***", 
                                             (255, 0, 255), 60)
                        destroyed_count = 0
                        for m in self.missiles[:]:
                            m_dist = math.sqrt((bullet['x'] - m['x'])**2 + 
                                             (bullet['y'] - m['y'])**2)
                            if m_dist < 450:
                                self.missiles.remove(m)
                                destroyed_count += 1
                                self.score += int(100 * self.combo_multiplier)
                                self.total_hits += 1
                                self.create_explosion(m['x'], m['y'], 60, (255, 150, 255))
                        if destroyed_count > 0:
                            self.add_floating_text(640, 320, 
                                                 f"x{destroyed_count} DESTROYED!", 
                                                 (255, 100, 255), 48)

                    elif bullet['type'] == 'grenade':
                        self.create_explosion(bullet['x'], bullet['y'], 180, (255, 120, 0))
                        for m in self.missiles[:]:
                            m_dist = math.sqrt((bullet['x'] - m['x'])**2 + 
                                             (bullet['y'] - m['y'])**2)
                            if m_dist < 180 and m != missile:
                                self.missiles.remove(m)
                                self.score += int(100 * self.combo_multiplier)
                                self.total_hits += 1
                                self.update_combo(dt, True)

                    elif bullet['type'] == 'shotgun':
                        self.create_explosion(missile['x'], missile['y'], 50, (255, 220, 80))

                    else:
                        exp_color = (255, 255, 120) # Default Standard (Giallo)
                        exp_radius = 70
                        
                        if missile['type'] == 'fast':
                            exp_color = (0, 255, 255)   # Ciano
                            exp_radius = 50             # Più piccola e rapida
                        elif missile['type'] == 'heavy':
                            exp_color = (255, 50, 0)    # Rosso sangue
                            exp_radius = 110            # Enorme
                        elif missile['type'] == 'jitter':
                            exp_color = (255, 0, 255)   # Viola
                            exp_radius = 60

                        self.create_explosion(missile['x'], missile['y'], exp_radius, exp_color)


                    self.add_floating_text(missile['x'], missile['y'] - 20, 
                                         f"+{points}", (255, 255, 100), 28)
                    self.spawn_powerup(missile['x'], missile['y'])
                    self.update_combo(dt, True)
                    self.missiles_destroyed_this_wave += 1
                    self.synth.create_score_point().play()
                    hit = True
                    break

            if hit and bullet in self.bullets:
                self.bullets.remove(bullet)

        for pu in self.powerups[:]:
            pu['y'] += pu['vy'] * dt
            pu['pulse'] += dt * 6
            pu['rotation'] += dt * 180

            if pu['y'] > 720:
                self.powerups.remove(pu)
                continue

            for bullet in self.bullets[:]:
                if 'x' in bullet:
                    dist = math.sqrt((bullet['x'] - pu['x'])**2 + 
                                   (bullet['y'] - pu['y'])**2)
                    if dist < 40:
                        if pu['type'] == 'life':
                            self.health = min(self.max_health, self.health + 1)
                            destroyed_cities = [c for c in self.cities if not c['alive']]
                            if destroyed_cities:
                                city_to_rebuild = destroyed_cities[0]
                                city_to_rebuild['alive'] = True
                                city_to_rebuild['windows'] = self.generate_windows()
                                self.add_floating_text(city_to_rebuild['x'], 
                                                     city_to_rebuild['y'] - 50,
                                                     "CITY REBUILT!", 
                                                     (0, 255, 120), 40)
                        else:
                            self.active_powerup = pu['type']
                            self.powerup_ammo = 25 if pu['type'] == 'shotgun' else 15

                        self.create_explosion(pu['x'], pu['y'], 55, pu['color'])
                        self.powerups.remove(pu)
                        self.synth.create_score_point().play()
                        break

        if self.missiles_destroyed_this_wave >= self.missiles_needed_for_wave:
            self.wave += 1
            self.missiles_destroyed_this_wave = 0
            self.missiles_needed_for_wave += 4
            self.add_floating_text(640, 200, f"WAVE {self.wave}!", (100, 255, 255), 72)

            alive_count = sum(1 for c in self.cities if c['alive'])
            bonus = alive_count * 500
            if bonus > 0:
                self.score += bonus
                self.add_floating_text(640, 280, f"Cities Bonus: +{bonus}", 
                                     (100, 255, 100), 48)

        return True






    def draw_gameover(self, surface):
        """Schermata Game Over professionale con statistiche"""
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        surface.blit(overlay, (0, 0))
        
        # GAME OVER con ombra epica
        font_huge = pygame.font.Font(None, 100)
        for offset in [(-3, -3), (3, -3), (-3, 3), (3, 3)]:
            shadow = font_huge.render("GAME OVER", True, (100, 0, 0))
            surface.blit(shadow, (640 - shadow.get_width() // 2 + offset[0], 160 + offset[1]))
        
        go_surf = font_huge.render("GAME OVER", True, (255, 100, 100))
        surface.blit(go_surf, (640 - go_surf.get_width() // 2, 160))
        
        # ✅ STATISTICHE CORRETTE
        font_stats = pygame.font.Font(None, 38)
        stats = [
            f"Final Score: {self.score}",
            f"Max Combo: x{self.max_combo}",      # ✅ CORRETTO
            f"Wave Reached: {self.wave}",         # ✅ CORRETTO
            f"Accuracy: {self.accuracy}%"
        ]
        
        y = 320
        for stat in stats:
            stat_surf = font_stats.render(stat, True, (220, 255, 220))
            surface.blit(stat_surf, (640 - stat_surf.get_width() // 2, y))
            y += 40
        
        # Hint lampeggiante
        hint_pulse = abs(math.sin(self.time * 4)) * 0.5 + 0.5
        hint_col = tuple(int(c * hint_pulse + (1 - hint_pulse) * 100) for c in (255, 255, 180))
        hint_surf = font_stats.render("RIGHT CLICK TO CONTINUE", True, hint_col)
        surface.blit(hint_surf, (640 - hint_surf.get_width() // 2, 570))






    def draw(self, surface):
        """Rendering principale del gioco"""
        if self.game_over:
            self._draw_background(surface)
            self._draw_cities(surface)
            self.draw_gameover(surface)
            return

        # Rendering in ordine di layer (dal background al foreground)
        self._draw_background(surface)
        self._draw_stars(surface)
        self._draw_meteors(surface)
        self._draw_ground(surface)
        self._draw_cities(surface)
        self._draw_explosions(surface)
        self._draw_particles(surface)
        self._draw_missiles(surface)
        self._draw_bullets(surface)
        self._draw_powerups(surface)
        self._draw_tank(surface)
        self._draw_charge_bar(surface)
        self._draw_floating_texts(surface)
        self._draw_hud(surface)




    def _draw_background(self, surface):
        """Disegna un cielo dinamico che copre TUTTO lo schermo (0-720px) e cambia col livello"""
        
        # Determina i colori target in base al livello (Wave)
        # Transizione graduale tra palette diverse
        if self.wave <= 2:
            # NOTTE PROFONDA (Classic Arcade)
            top_col = (10, 10, 25)      # Blu notte scuro
            bot_col = (25, 20, 40)      # Viola scuro orizzonte
        elif self.wave <= 4:
            # ALBA CYBERPUNK (Synthwave)
            top_col = (40, 20, 60)      # Viola
            bot_col = (180, 80, 60)     # Arancio neon
        elif self.wave <= 6:
            # TRAMONTO TOSSICO (Danger)
            top_col = (60, 20, 20)      # Rosso scuro
            bot_col = (160, 140, 40)    # Giallo acido
        else:
            # APOCALISSE (Endgame)
            top_col = (20, 5, 5)        # Quasi nero
            bot_col = (120, 20, 20)     # Rosso sangue
            
        # Gestione Cache: rigenera se cambia livello o dimensioni
        current_palette = (top_col, bot_col)
        
        # Controllo se dobbiamo rigenerare la surface di background
        if (not hasattr(self, '_bg_surface') or 
            not hasattr(self, '_last_bg_wave_palette') or 
            self._last_bg_wave_palette != current_palette):
            
            self._last_bg_wave_palette = current_palette
            
            # Altezza TOTALE dello schermo (non fermarti al terreno!)
            h = 720 
            self._bg_surface = pygame.Surface((1, h))
            
            r1, g1, b1 = top_col
            r2, g2, b2 = bot_col
            
            # Genera gradiente verticale
            for y in range(h):
                ratio = y / h
                # Interpolazione lineare (lerp)
                r = int(r1 * (1 - ratio) + r2 * ratio)
                g = int(g1 * (1 - ratio) + g2 * ratio)
                b = int(b1 * (1 - ratio) + b2 * ratio)
                self._bg_surface.set_at((0, y), (r, g, b))
        
        # Scala per riempire TUTTO lo schermo (0,0) -> (1280, 720)
        # Viene disegnato PRIMA di tutto, quindi ground e cities ci andranno sopra
        scaled_bg = pygame.transform.scale(self._bg_surface, surface.get_size())
        surface.blit(scaled_bg, (0, 0))


    def _draw_stars(self, surface):
        """Disegna le stelle con effetto twinkle"""
        for star in self.stars:
            twinkle = abs(math.sin(star['twinkle']))
            brightness = int(star['brightness'] * (0.5 + twinkle * 0.5))
            color = (brightness, brightness, brightness)
            if star['size'] == 1:
                try:
                    surface.set_at((int(star['x']), int(star['y'])), color)
                except:
                    pass
            else:
                pygame.draw.circle(surface, color, 
                                (int(star['x']), int(star['y'])), star['size'])






    def _draw_meteors(self, surface):
        """Meteore SFUMATE: trails soft + ESPLOSIONE PARTICELLARE finale visibile"""
        visible_meteors = [m for m in self.meteors if len(m['trail']) >= 3]
        
        for meteor in visible_meteors:
            trail = meteor['trail']
            hx, hy = trail[-1]
            if not (0 <= hx <= 1280 and 0 <= hy <= 720):
                continue
            
            trail_points = min(6, len(trail))
            
            for i in range(trail_points):
                px, py = trail[max(0, len(trail)-1-i)]
                
                fade = max(0.08, (1 - i/trail_points)**1.3)
                core_size = int(0.9 + fade * 1.4)
                
                if core_size >= 1:
                    # CORE + GLOW normale
                    base_bright = int(35 + 40 * fade)
                    shimmer = abs(math.sin(self.time * 1.8 + i * 0.4)) * 0.2
                    bright = int(base_bright * (1 + shimmer))
                    
                    color = (int(bright*0.92), int(bright*0.55), int(bright*1.15))
                    
                    for layer in range(2):
                        g_size = core_size + layer * 0.3
                        g_alpha = int(85 * fade * (0.75 - layer * 0.35))
                        if g_alpha < 12: continue
                        
                        gs = pygame.Surface((4, 4), pygame.SRCALPHA)
                        pygame.draw.circle(gs, (*color, g_alpha), (2, 2), int(g_size))
                        surface.blit(gs, (int(px)-2, int(py)-2), special_flags=pygame.BLEND_ADD)
                else:
                    # **ESPLOSIONE PARTICELLARE VISIBILE** (fadeout)
                    p_time = self.time + px * 0.01  # Offset per stagger
                    p_fade = max(0.02, fade * 0.6 * (1 - abs(math.sin(p_time * 4)) * 0.3))
                    
                    # 4 PARTICELLE piccole trasparenti
                    for p in range(4):
                        p_angle = p * 1.57  # 90° spread
                        p_dx = math.cos(p_angle) * 1.2
                        p_dy = math.sin(p_angle) * 1.2
                        p_x, p_y = px + p_dx, py + p_dy
                        
                        p_bright = int(18 + 12 * p_fade)
                        p_color = (int(p_bright*1.1), int(p_bright*0.7), int(p_bright*1.3))
                        p_alpha = int(55 * p_fade)
                        
                        p_gs = pygame.Surface((3, 3), pygame.SRCALPHA)
                        pygame.draw.circle(p_gs, (*p_color, p_alpha), (1.5, 1.5), 1)
                        surface.blit(p_gs, (int(p_x)-1, int(p_y)-1), special_flags=pygame.BLEND_ADD)










    def _draw_ground(self, surface):
        """Disegna un terreno Cyberpunk dettagliato con griglia prospettica e texture"""
        ground_h = 60
        ground_y = 660
        width = surface.get_width()

        # 1. Base terreno (Gradiente scuro solido per coprire sfondo)
        pygame.draw.rect(surface, (15, 10, 20), (0, ground_y, width, ground_h))

        # 2. Griglia prospettica "Synthwave"
        # Linee orizzontali (più fitte verso l'alto per prospettiva)
        horiz_lines = [0, 8, 18, 30, 44]
        for y_off in horiz_lines:
            # Colore che sfuma dal viola al blu scuro
            line_color = (120 - y_off, 60, 160) 
            y = ground_y + y_off
            pygame.draw.line(surface, line_color, (0, y), (width, y), 1)

        # Linee verticali (in prospettiva verso un punto di fuga centrale)
        center_x = width // 2
        # Disegna linee ogni 80px alla base
        for i in range(-12, 13):
            base_offset = i * 80
            # Punto in alto (orizzonte) converge verso il centro (0.6x)
            top_x = center_x + base_offset * 0.6
            # Punto in basso (fondo schermo) diverge (1.4x)
            bot_x = center_x + base_offset * 1.4

            # Linee sottili viola scuro
            pygame.draw.line(surface, (70, 40, 100), (top_x, ground_y), (bot_x, ground_y + ground_h), 1)

        # 3. Dettagli Superficie (Texture procedurale deterministica)
        # Usa coordinate X per determinare dove disegnare "rocce" digitali
        for x in range(0, width, 20):
            # Pseudo-random deterministico basato sulla posizione
            if (x * 13 + 7) % 7 == 0: 
                h_rock = 4 + (x % 5)
                # Blocco scuro (roccia)
                pygame.draw.rect(surface, (35, 30, 45), (x, ground_y, 12, 6))
                # Highlight bordo superiore
                pygame.draw.line(surface, (60, 50, 70), (x, ground_y), (x+12, ground_y), 1)
            elif (x * 11) % 13 == 0:
                # Dettaglio "Tech" (piccolo led o cavo)
                pygame.draw.rect(surface, (20, 15, 25), (x+4, ground_y+2, 6, 4))
                if (x % 100) > 50: # Alcuni hanno un punto luce
                    pygame.draw.circle(surface, (100, 50, 50), (x+7, ground_y+4), 1)

        # 4. Linea di separazione superiore (Orizzonte neon con glow)
        # Linea principale luminosa
        pygame.draw.line(surface, (200, 50, 220), (0, ground_y), (width, ground_y), 2)

        # Effetto Glow simulato (linee semitrasparenti sotto)
        # Nota: disegniamo linee dirette per performance invece di surface con alpha
        pygame.draw.line(surface, (150, 40, 150), (0, ground_y + 2), (width, ground_y + 2), 1)
        pygame.draw.line(surface, (80, 20, 80), (0, ground_y + 3), (width, ground_y + 3), 1)


    def _draw_cities(self, surface):
        """Disegna tutte le città gestendo alive/destroyed"""
        # Batch drawing could be optimized here if needed, but loop is fine for <10 cities
        for city in self.cities:
            if city['alive']:
                self._draw_city_alive(surface, city)
            else:
                self._draw_city_destroyed(surface, city)


    def _draw_city_alive(self, surface, city):
        """Disegna una città futuristica dettagliata e viva"""
        city_x = city['x']
        city_y = city['y']
        width = city['width']
        height = city['height']

        # Palette Colori (Cyberpunk)
        is_sky = city['type'] == 'skyscraper'
        c_base = (35, 40, 50) if is_sky else (50, 45, 40)
        c_shadow = (20, 25, 30)
        c_outline = (60, 70, 80)
        c_win_lit = (255, 245, 180) if is_sky else (255, 120, 60) # Giallo vs Arancio industriale
        c_win_dim = (25, 30, 40)
        c_neon = (0, 230, 255) if is_sky else (255, 80, 0) # Cyan vs Orange Neon

        # 1. Ombra riflessa a terra
        shadow_rect = (city_x - width//2 - 8, city_y - 3, width + 16, 6)
        pygame.draw.ellipse(surface, (10, 10, 15), shadow_rect)

        # 2. Struttura Principale (Building Body)
        main_rect = (city_x - width//2, city_y - height, width, height)
        pygame.draw.rect(surface, c_base, main_rect)

        # Dettaglio profondità laterale (Finto 3D sulla destra)
        depth_w = 6
        pygame.draw.rect(surface, c_shadow, (city_x + width//2, city_y - height + 4, depth_w, height - 4))

        # Outline tech
        pygame.draw.rect(surface, c_outline, main_rect, 2)

        # 3. Finestre (Griglia procedurale)
        cols = 3
        rows = 4
        win_w = (width - 12) // cols
        win_h = (height - 12) // rows

        for r in range(rows):
            for c in range(cols):
                # Hash deterministico per stato luci (stabile per ogni frame)
                # Usa coordinate e indice per varietà
                seed = (city_x // 10) + r * 7 + c * 3
                is_lit = (seed % 3 != 0) # ~66% accese

                wx = city_x - width//2 + 5 + c * (win_w + 2)
                wy = city_y - height + 6 + r * (win_h + 2)

                color = c_win_lit if is_lit else c_win_dim
                pygame.draw.rect(surface, color, (wx, wy, win_w, win_h))

                # Micro-dettaglio: riflesso su finestra accesa
                if is_lit:
                    pygame.draw.line(surface, (255, 255, 255), (wx, wy), (wx+1, wy+1), 1)

        # 4. Dettagli Unici per Tipo
        if is_sky:
            # --- SKYSCRAPER: Antenna & Neon ---
            # Striscia neon alla base
            pygame.draw.rect(surface, c_neon, (city_x - width//2 + 2, city_y - 4, width - 4, 2))

            # Antenna sul tetto
            ant_h = 14
            pygame.draw.line(surface, c_outline, (city_x - 5, city_y - height), (city_x - 5, city_y - height - ant_h + 4), 2)
            pygame.draw.line(surface, (150, 150, 150), (city_x - 5, city_y - height - ant_h + 4), (city_x - 5, city_y - height - ant_h), 1)

            # Luce rossa lampeggiante (usando ticks globali)
            if (pygame.time.get_ticks() // 600) % 2 == 0:
                pygame.draw.line(surface, (255, 50, 50), (city_x - 6, city_y - height - ant_h), (city_x - 4, city_y - height - ant_h), 2)

        else:
            # --- FACTORY: Ciminiere & Fumo ---
            chim_w = 10
            chim_h = 14
            cx = city_x - width//2 + 6
            cy = city_y - height - chim_h

            # Ciminiere
            pygame.draw.rect(surface, (70, 60, 60), (cx, cy, chim_w, chim_h))
            pygame.draw.rect(surface, (40, 35, 35), (cx + 2, cy + 2, chim_w - 4, chim_h)) # Interno

            # Banda di pericolo gialla/nera
            pygame.draw.line(surface, (200, 180, 50), (cx, cy + 4), (cx + chim_w, cy + 4), 2)

            # Particelle fumo (deterministico basato sul tempo per non creare oggetti)
            # Simula 3 particelle che salgono ciclicamente
            import math
            t = pygame.time.get_ticks() / 1000.0
            for i in range(3):
                offset = i * 2.0
                cycle = (t + offset) % 3.0 # Ciclo di 3 secondi
                if cycle < 2.0: # Visibile per 2 secondi
                    alpha_factor = 1.0 - (cycle / 2.0) # Svanisce salendo
                    sy = cy - (cycle * 15) # Sale di 15px
                    sx = cx + 5 + math.sin(t * 2 + i) * 3 # Ondula

                    # Colore grigio che svanisce (simulato scurendo)
                    col_val = int(80 * alpha_factor)
                    if col_val > 10:
                        pygame.draw.circle(surface, (col_val, col_val, col_val), (int(sx), int(sy)), int(2 + cycle))


    def _draw_city_destroyed(self, surface, city):
        """Disegna le rovine di una città (Macerie fumanti)"""
        city_x = city['x']
        city_y = city['y']
        width = city['width']

        # 1. Cumulo di macerie (Poligono frastagliato)
        # Silhouette irregolare
        rubble_pts = [
            (city_x - width//2, city_y),
            (city_x - width//3, city_y - 8),
            (city_x - width//6, city_y - 4),
            (city_x, city_y - 12),
            (city_x + width//4, city_y - 6),
            (city_x + width//2, city_y)
        ]
        pygame.draw.polygon(surface, (40, 35, 35), rubble_pts)

        # Highlight bordi rotti
        pygame.draw.lines(surface, (60, 50, 50), False, rubble_pts[1:-1], 2)

        # 2. Travi metalliche esposte (Linee che escono)
        pygame.draw.line(surface, (20, 20, 20), (city_x - 10, city_y), (city_x - 15, city_y - 18), 2)
        pygame.draw.line(surface, (20, 20, 20), (city_x + 5, city_y - 5), (city_x + 12, city_y - 20), 2)

        # 3. Effetto "Brace ardenti" (Punti rossi/arancio randomici)
        # Usiamo pseudo-random per sfarfallio
        import random
        # Genera 2-3 punti caldi che cambiano posizione leggermente
        if random.random() < 0.8:
            fx = city_x + random.randint(-15, 15)
            fy = city_y - random.randint(2, 12)
            pygame.draw.rect(surface, (255, 100 + random.randint(0, 100), 0), (fx, fy, 2, 2))

        # 4. Fumo scuro (Cerchi semplici che salgono)
        # Solo se distrutta di recente (< 10 sec) o sempre per atmosfera
        # Qui usiamo un semplice effetto probabilistico per non pesare
        if random.random() < 0.2:
            sx = city_x + random.randint(-10, 10)
            sy = city_y - 10 - random.randint(0, 15)
            pygame.draw.circle(surface, (30, 30, 35), (sx, sy), random.randint(3, 6))



    def _draw_explosions(self, surface):
        """Disegna tutte le esplosioni attive"""
        for exp in self.explosions:
            alpha = exp['lifetime'] / exp['max_lifetime']
            radius = int(exp['radius'])
            for i in range(5):
                r = radius - i * int(radius / 6)
                if r > 0:
                    intensity = alpha * (1 - i * 0.15)
                    color = tuple(int(c * intensity) for c in exp['color'])
                    pygame.draw.circle(surface, color, 
                                    (int(exp['x']), int(exp['y'])), r, 
                                    max(2, int(r / 10)))

    def _draw_particles(self, surface):
        """Disegna tutte le particelle con glow"""
        for p in self.particles:
            alpha = p['lifetime'] / p['max_lifetime']
            size = int(p['size'] * alpha)
            if size > 0:
                if p['fade']:
                    color = tuple(int(c * alpha) for c in p['color'])
                else:
                    color = p['color']
                pygame.draw.circle(surface, color, 
                                (int(p['x']), int(p['y'])), size)
                if size > 2:
                    glow_color = tuple(int(c * alpha * 0.5) for c in p['color'])
                    pygame.draw.circle(surface, glow_color, 
                                    (int(p['x']), int(p['y'])), size + 2)






    def _draw_missiles(self, surface):
        """
        Renderizza missili con geometria procedurale avanzata, effetti bloom e scie dinamiche.
        Ogni tipo di missile ha un design unico (High-Precision Rendering).
        """
        # Surface per effetti luminosi (Additive Blending)
        # Se troppo pesante su hardware vecchio, rimuovi il flag BLEND_ADD e usa alpha normale
        glow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        
        current_time = pygame.time.get_ticks()

        for missile in self.missiles:
            m_type = missile.get('type', 'standard')
            
            # --- CONFIGURAZIONE STILE & GEOMETRIA ---
            if m_type == 'fast':       # IPERSONICO (Sottile, Ali a delta)
                body_color = (200, 255, 255)
                trim_color = (0, 100, 150)
                glow_color = (0, 255, 255)
                length, width = 28, 6
                wing_span = 10
                engine_pulse_speed = 0.05
                
            elif m_type == 'heavy':    # ICBM (Grosso, cilindrico, alette piccole)
                body_color = (200, 200, 200) # Metallo grezzo
                trim_color = (180, 50, 50)   # Testata rossa
                glow_color = (255, 60, 0)
                length, width = 36, 14
                wing_span = 18
                engine_pulse_speed = 0.01

            elif m_type == 'jitter':   # ALIENO (Energia instabile, forma cristallina)
                body_color = (240, 200, 255)
                trim_color = (100, 0, 100)
                glow_color = (255, 0, 255)
                length, width = 24, 10
                wing_span = 14
                engine_pulse_speed = 0.2
                
            else:                      # STANDARD (Missile tattico bilanciato)
                body_color = (240, 240, 220)
                trim_color = (80, 80, 80)
                glow_color = (255, 200, 50)
                length, width = 26, 9
                wing_span = 16
                engine_pulse_speed = 0.03

            # --- 1. RENDERING SCIA (TRAIL) ---
            points = missile['trail']
            if len(points) > 1:
                # Ottimizzazione: Disegna la scia come strip di poligoni o linee con spessore variabile
                for i in range(len(points) - 1):
                    p_curr = points[i]
                    p_next = points[i+1]
                    
                    progress = i / len(points) # 0.0 (coda) -> 1.0 (testa)
                    
                    # Alpha quadratico (Fade-out morbido in coda)
                    alpha = int(180 * (progress ** 2))
                    if alpha <= 0: continue
                    
                    # Colore interpolato (Bianco caldissimo vicino al motore -> Colore scuro in coda)
                    if progress > 0.8:
                        seg_color = (255, 255, 200, alpha) # Nucleo caldo
                    else:
                        seg_color = glow_color + (alpha,)  # Fumo colorato
                    
                    # Spessore che si assottiglia in coda
                    seg_width = max(1, int(width * 0.8 * progress))
                    
                    # Jitter Effect sulla scia (solo per tipo 'jitter')
                    if m_type == 'jitter' and i % 2 == 0:
                        jit_off = math.sin(i * 0.8 + current_time * 0.02) * 3
                        p_curr = (p_curr[0] + jit_off, p_curr[1])

                    pygame.draw.line(glow_surf, seg_color, p_curr, p_next, seg_width)


            # --- 2. CALCOLO GEOMETRIA RUOTATA ---
            mx, my = missile['x'], missile['y']
            vx, vy = missile.get('vx', 0), missile.get('vy', 1)
            
            # Angolo di rotazione (in radianti)
            # atan2(y, x) -> +90° perché i poligoni base puntano a destra (0°) ma vy va in giù
            angle = math.atan2(vy, vx)
            cos_a, sin_a = math.cos(angle), math.sin(angle)

            def rot(lx, ly):
                """Ruota punto locale (lx, ly) e trasla a mondo (mx, my)"""
                return (mx + lx * cos_a - ly * sin_a, 
                        my + lx * sin_a + ly * cos_a)

            # --- 3. COSTRUZIONE SHAPE ---
            # Definiamo i punti in coordinate locali (X lung, Y larghezza)
            # X=0 è il centro del missile, X>0 è la punta, X<0 è la coda
            
            shapes = [] # Lista di poligoni (color, points)

            if m_type == 'fast':
                # Design: Ago volante con ali a delta posteriori
                shapes.append((body_color, [
                    rot(length/2, 0),         # Punta
                    rot(-length/2, -width/2), # Coda alta
                    rot(-length/2 + 4, 0),    # Incavo motore
                    rot(-length/2, width/2)   # Coda bassa
                ]))
                # Cockpit/Dettaglio scuro
                shapes.append((trim_color, [
                    rot(length/4, 0), rot(0, -width/4), rot(0, width/4)
                ]))

            elif m_type == 'heavy':
                # Design: Ogiva grossa, corpo cilindrico
                # Corpo principale
                shapes.append((body_color, [
                    rot(length/2 - 5, -width/2), rot(length/2 - 5, width/2), # Base ogiva
                    rot(-length/2, width/2), rot(-length/2, -width/2)        # Fondo
                ]))
                # Ogiva (Testata)
                shapes.append((trim_color, [
                    rot(length/2, 0),              # Punta estrema
                    rot(length/2 - 5, -width/2),   # Spalla alta
                    rot(length/2 - 5, width/2)     # Spalla bassa
                ]))
                # Alette piccole posteriori
                shapes.append(((100, 100, 100), [
                    rot(-length/2 + 8, 0),
                    rot(-length/2, -wing_span),
                    rot(-length/2, wing_span)
                ]))

            elif m_type == 'jitter':
                # Design: Cristallo asimmetrico
                pulse = math.sin(current_time * 0.01 + missile.get('jitter_phase', 0)) * 2
                shapes.append((body_color, [
                    rot(length/2, 0),
                    rot(0, -width/2 - pulse),
                    rot(-length/3, 0),
                    rot(0, width/2 + pulse)
                ]))
                # Nucleo energetico centrale
                shapes.append(((255, 255, 255), [
                    rot(5, 0), rot(-5, -3), rot(-5, 3)
                ]))

            else: # STANDARD
                # Design: Razzo classico con pinne a croce
                # Corpo
                shapes.append((body_color, [
                    rot(length/2, 0),          # Punta
                    rot(length/4, -width/2),   # Spalla
                    rot(-length/2, -width/2),  # Coda
                    rot(-length/2, width/2),
                    rot(length/4, width/2)
                ]))
                # Pinne
                shapes.append((trim_color, [
                    rot(-length/2 + 5, 0),
                    rot(-length/2, -wing_span),
                    rot(-length/2 + 10, 0),
                    rot(-length/2, wing_span)
                ]))

            # --- 4. DISEGNO SHAPES ---
            for color, pts in shapes:
                pygame.draw.polygon(surface, color, pts)
                # Outline sottile per definizione
                pygame.draw.polygon(surface, (50, 50, 50), pts, 1)

            # --- 5. MOTORE & GLOW (Effetti Luce) ---
            # Posizione scarico motore
            engine_pos = rot(-length/2, 0)
            
            # Pulsazione motore
            pulse = (math.sin(current_time * engine_pulse_speed) + 1) * 0.5 # 0.0 -> 1.0
            
            # Bagliore diffuso (Halo)
            glow_radius = int(width * 1.5 + pulse * 4)
            # Disegna su glow_surf per blending
            pygame.draw.circle(glow_surf, glow_color + (80,), (int(engine_pos[0]), int(engine_pos[1])), glow_radius)
            
            # Nucleo motore caldissimo (Bianco)
            core_radius = int(width * 0.4 + pulse * 2)
            pygame.draw.circle(surface, (255, 255, 255), (int(engine_pos[0]), int(engine_pos[1])), core_radius)

            # Cono di spinta (Thrust Cone) - Opzionale per dettaglio extra
            thrust_len = 10 + pulse * 5
            thrust_pts = [
                rot(-length/2, width/4),
                rot(-length/2, -width/4),
                rot(-length/2 - thrust_len, 0) # Punta della fiamma
            ]
            pygame.draw.polygon(glow_surf, glow_color + (150,), thrust_pts)

        # Blit finale degli effetti di luce (Blending additivo se possibile, altrimenti alpha standard)
        # surface.blit(glow_surf, (0, 0), special_flags=pygame.BLEND_ADD) 
        # BLEND_ADD è bellissimo ma su alcuni sistemi/surface vecchi può dare problemi con l'alpha.
        # Se vedi rettangoli neri attorno ai glow, togli special_flags.
        surface.blit(glow_surf, (0, 0))






    def _draw_bullets(self, surface):
        """Disegna tutti i proiettili del giocatore"""
        for bullet in self.bullets:
            # Laser speciale
            if bullet['type'] == 'laser':
                self._draw_laser_beam(surface, bullet)
                continue

            # Scia per proiettili normali
            if 'trail' in bullet:
                for i, (tx, ty) in enumerate(bullet['trail']):
                    if len(bullet['trail']) > 0:
                        alpha = i / len(bullet['trail'])
                        size = int(2 + alpha * 6)
                        pygame.draw.circle(surface, bullet['color'], 
                                        (int(tx), int(ty)), size)

            # Corpo proiettile
            size = bullet.get('size', 9)
            if bullet['type'] == 'super_grenade':
                size = 15
                if 'glow' in bullet:
                    glow_size = int(size + abs(math.sin(bullet['glow'])) * 12)
                    pygame.draw.circle(surface, (255, 100, 255), 
                                    (int(bullet['x']), int(bullet['y'])), glow_size)

            pygame.draw.circle(surface, bullet['color'], 
                            (int(bullet['x']), int(bullet['y'])), size)
            pygame.draw.circle(surface, (255, 255, 255), 
                            (int(bullet['x']), int(bullet['y'])), max(1, size - 4))

    def _draw_laser_beam(self, surface, bullet):
        """Disegna un raggio laser con effetti glow"""
        width = bullet.get('beam_width', 10)
        for i in range(5, 0, -1):
            pygame.draw.line(surface, (0, 255 - i*30, 255),
                        (int(bullet['x1']), int(bullet['y1'])),
                        (int(bullet['x2']), int(bullet['y2'])), 
                        width + i * 5)
        pygame.draw.line(surface, (255, 255, 255),
                    (int(bullet['x1']), int(bullet['y1'])),
                    (int(bullet['x2']), int(bullet['y2'])), 
                    max(3, width))

    def _draw_powerups(self, surface):
        """Disegna tutti i powerup con effetti glow e rotazione"""
        for pu in self.powerups:
            pulse_size = abs(math.sin(pu['pulse'])) * 12

            # Anelli glow
            for i in range(5, 0, -1):
                glow_color = tuple(max(0, c - i * 40) for c in pu['color'])
                pygame.draw.circle(surface, glow_color, 
                                (int(pu['x']), int(pu['y'])), 
                                int(28 + i * 10 + pulse_size), 2)

            # Esagono rotante
            center_x, center_y = int(pu['x']), int(pu['y'])
            points = []
            for i in range(6):
                angle = math.radians(60 * i + pu['rotation'])
                px = center_x + math.cos(angle) * 22
                py = center_y + math.sin(angle) * 22
                points.append((px, py))

            pygame.draw.polygon(surface, (0, 0, 0), points)
            pygame.draw.polygon(surface, pu['color'], points, 5)

            # Icona tipo powerup
            font = pygame.font.Font(None, 32)
            icons = {'shotgun': 'S', 'laser': 'L', 'grenade': 'G', 'life': '+'}
            text = font.render(icons[pu['type']], True, (255, 255, 255))
            surface.blit(text, (center_x - text.get_width()//2, 
                            center_y - text.get_height()//2))



    def _draw_tank(self, surface):
        """Tank Heavy Sci-Fi con simmetria perfetta e laser corretto (All-in-One)"""
        tank_x = self.tank_x
        tank_y = self.tank_y
        rad = math.radians(self.tank_angle)

        # --- PALETTE COLORI ---
        c_track = (28, 30, 36)
        c_track_hi = (70, 75, 85)
        c_track_edge = (10, 10, 12)
        c_hull_dark = (45, 55, 65)
        c_hull_mid = (70, 82, 95)
        c_hull_edge = (20, 25, 30)
        c_metal = (145, 155, 165)

        # --- OMBRA ---
        # Creiamo surface temporanea al volo per l'ombra con alpha
        shadow_surf = pygame.Surface((110, 34), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 90), (0, 0, 110, 34))
        surface.blit(shadow_surf, (tank_x - 55, tank_y - 6))

        # --- CINGOLI SIMMETRICI ---
        # Parametri condivisi per perfetta simmetria
        track_dx = 30     # Distanza dal centro
        track_w = 22      # Larghezza cingolo
        track_h = 42      # Altezza cingolo
        track_top = tank_y - 24

        # Offset animazione
        track_anim_offset = int(self.tank_tracks_offset) % 14

        # Loop per disegnare Sinistra (-1) e Destra (+1) identici
        for side in [-1, 1]:
            # Calcolo X per questo lato: centro + (direzione * distanza) - metà larghezza
            # side -1: tank_x - 30 - 11
            # side +1: tank_x + 30 - 11
            tx = tank_x + (side * track_dx) - (track_w // 2)

            # 1. Corpo cingolo
            pygame.draw.rect(surface, c_track, (tx, track_top, track_w, track_h), border_radius=6)
            pygame.draw.rect(surface, c_track_edge, (tx, track_top, track_w, track_h), 2, border_radius=6)

            # 2. Belt interna scura
            inner_m = 3 # Margine interno
            pygame.draw.rect(surface, (18, 18, 22), 
                            (tx + inner_m, track_top + inner_m, track_w - inner_m*2, track_h - inner_m*2), 
                            border_radius=5)

            # 3. Segmenti animati (Treads)
            seg_h = 6
            seg_step = 9
            usable_h = track_h - (inner_m * 2)

            # Disegna segmenti ciclici
            # Usiamo range abbondante e modulo per l'effetto scorrimento continuo
            for i in range(0, usable_h // seg_step + 2):
                # Calcolo Y relativo all'interno del cingolo
                rel_y = (i * seg_step - track_anim_offset) % usable_h
                abs_y = track_top + inner_m + rel_y

                # Evita di disegnare fuori dall'area utile (opzionale con clipping, ma qui calcoliamo preciso)
                if abs_y + seg_h <= track_top + track_h - inner_m:
                    pygame.draw.rect(surface, c_track_hi,
                                (tx + inner_m + 1, abs_y, track_w - (inner_m * 2) - 2, seg_h),
                                border_radius=3)

            # 4. Ruote interne (dettaglio meccanico)
            cx = tx + track_w // 2
            for i in range(3):
                wy = track_top + 10 + (i * 11)
                pygame.draw.circle(surface, (12, 12, 14), (cx, wy), 6)
                pygame.draw.circle(surface, (70, 75, 85), (cx, wy), 2)

        # --- CHASSIS CENTRALE ---
        hull_w = 54
        hull_h = 34
        hull_x = tank_x - hull_w // 2
        hull_y = tank_y - 22

        # Scafo principale
        pygame.draw.rect(surface, c_hull_dark, (hull_x, hull_y, hull_w, hull_h), border_radius=6)
        pygame.draw.rect(surface, c_hull_edge, (hull_x, hull_y, hull_w, hull_h), 2, border_radius=6)

        # Piastra superiore (Dettaglio geometrico)
        plate_pts = [
            (tank_x - 18, hull_y + 3),
            (tank_x + 22, hull_y + 3),
            (tank_x + 16, hull_y + 22),
            (tank_x - 22, hull_y + 22),
        ]
        pygame.draw.polygon(surface, c_hull_mid, plate_pts)
        pygame.draw.polygon(surface, c_hull_edge, plate_pts, 1)

        # Dettagli bulloni
        for bx in (-14, -4, 6, 16):
            pygame.draw.circle(surface, (25, 30, 35), (tank_x + bx, hull_y + 10), 2)

        # --- TORRETTA E CANNONE ---
        pivot_x = tank_x
        pivot_y = tank_y - 6

        # Funzione rotazione inline per evitare dipendenze
        def rotate_xy(px, py):
            dx = px - pivot_x
            dy = py - pivot_y
            rx = dx * math.cos(rad) - dy * math.sin(rad)
            ry = dx * math.sin(rad) + dy * math.cos(rad)
            return (pivot_x + rx, pivot_y + ry)

        # 1. Torretta base (Sotto il cannone)
        pygame.draw.circle(surface, c_hull_mid, (pivot_x, pivot_y), 14)
        pygame.draw.circle(surface, c_hull_edge, (pivot_x, pivot_y), 14, 2)

        # 2. Canna (Body)
        barrel_len = 52
        barrel_w = 10
        raw_barrel = [
            (pivot_x, pivot_y - barrel_w/2),
            (pivot_x + barrel_len, pivot_y - barrel_w/2),
            (pivot_x + barrel_len, pivot_y + barrel_w/2),
            (pivot_x, pivot_y + barrel_w/2),
        ]
        rot_barrel = [rotate_xy(x, y) for x, y in raw_barrel]
        pygame.draw.polygon(surface, c_metal, rot_barrel)
        pygame.draw.polygon(surface, c_hull_edge, rot_barrel, 1)

        # 3. Punta cannone (Muzzle block)
        muz_len = 8
        raw_muz = [
            (pivot_x + barrel_len, pivot_y - 8),
            (pivot_x + barrel_len + muz_len, pivot_y - 8),
            (pivot_x + barrel_len + muz_len, pivot_y + 8),
            (pivot_x + barrel_len, pivot_y + 8),
        ]
        rot_muz = [rotate_xy(x, y) for x, y in raw_muz]
        pygame.draw.polygon(surface, c_hull_mid, rot_muz)
        pygame.draw.polygon(surface, c_hull_edge, rot_muz, 1)

        # 4. Dettaglio centrale torretta
        pygame.draw.circle(surface, (20, 22, 26), (pivot_x, pivot_y), 6)

        # --- LASER SFUMATO (Integrato) ---
        if not self.game_over:
            # Start point (punta cannone)
            start_dist = barrel_len + muz_len
            sx = pivot_x + math.cos(rad) * start_dist
            sy = pivot_y + math.sin(rad) * start_dist

            # Parametri laser
            laser_len = 260
            steps = 10
            dx = math.cos(rad)
            dy = math.sin(rad)

            # Surface temporanea per blending Alpha
            # Creiamo una surface grande quanto lo schermo per semplicità di blit
            # (Per ottimizzazione estrema si potrebbe fare piccola e ruotarla, ma questo è più sicuro)
            fx_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

            # Disegna segmenti con alpha decrescente
            for i in range(steps):
                t0 = i / steps
                t1 = (i + 1) / steps

                # Coordinate segmento
                x0 = sx + dx * (laser_len * t0)
                y0 = sy + dy * (laser_len * t0)
                x1 = sx + dx * (laser_len * t1)
                y1 = sy + dy * (laser_len * t1)

                # Alpha decrescente (Fade Out)
                alpha = int(170 * (1.0 - t0))  # Da 170 a 0

                # Spessore variabile (più sottile alla fine)
                width = 3 if i < 2 else (2 if i < 6 else 1)

                # Beam principale Rosso
                pygame.draw.line(fx_surf, (255, 40, 40, alpha), (x0, y0), (x1, y1), width)

                # Core Bianco (solo all'inizio)
                if i < 3:
                    core_alpha = min(200, alpha + 40)
                    pygame.draw.line(fx_surf, (255, 220, 220, core_alpha), (x0, y0), (x1, y1), 1)

            # Blit finale del laser sulla surface principale
            surface.blit(fx_surf, (0, 0))




    def _draw_charge_bar(self, surface):
        """Disegna la barra di carica del nuke"""
        if not self.first_shot_fired or self.charge_time < self.min_charge_display:
            return

        charge_percent = min(1.0, self.charge_time / self.max_charge_time)
        bar_width = 220
        bar_height = 20
        bar_x = self.tank_x - bar_width // 2
        bar_y = self.tank_y - 90

        # Container
        pygame.draw.rect(surface, (20, 20, 20), 
                    (bar_x - 3, bar_y - 3, bar_width + 6, bar_height + 6))
        pygame.draw.rect(surface, (40, 40, 40), 
                    (bar_x, bar_y, bar_width, bar_height))

        # Fill colorato
        fill_width = int(bar_width * charge_percent)
        if charge_percent < 0.5:
            color = (255, int(255 * charge_percent * 2), 0)
        elif charge_percent < 1.0:
            color = (255, 255, int((charge_percent - 0.5) * 510))
        else:
            flash = abs(math.sin(self.time * 15))
            color = (255, int(50 + flash * 205), 255)

        pygame.draw.rect(surface, color, 
                    (bar_x, bar_y, fill_width, bar_height))
        pygame.draw.rect(surface, (200, 200, 200), 
                    (bar_x, bar_y, bar_width, bar_height), 3)

        # Testo
        font = pygame.font.Font(None, 28)
        if charge_percent >= 1.0:
            text = font.render("NUKE READY - RELEASE TO FIRE!", True, (255, 50, 255))
        else:
            text = font.render(f"Charging: {int(charge_percent * 100)}%", 
                            True, (255, 255, 255))
        surface.blit(text, (bar_x + bar_width//2 - text.get_width()//2, bar_y - 35))

    def _draw_floating_texts(self, surface):
        """Disegna i testi fluttuanti (combo, punteggi, etc)"""
        for txt in self.floating_texts:
            alpha = txt['lifetime'] / txt['max_lifetime']
            font = pygame.font.Font(None, txt['size'])
            text_surf = font.render(txt['text'], True, txt['color'])
            if alpha < 0.3:
                text_surf.set_alpha(int(alpha / 0.3 * 255))
            surface.blit(text_surf, (int(txt['x']) - text_surf.get_width()//2, 
                                int(txt['y'])))

    def _draw_hud(self, surface):
        """Disegna l'HUD completo (score, health, combo, powerup, etc)"""
        font_score = pygame.font.Font(None, 52)
        font_medium = pygame.font.Font(None, 32)
        font_small = pygame.font.Font(None, 24)
        font_combo_big = pygame.font.Font(None, 44)

        def draw_text_shadow(text, font, x, y, color, shadow_offset=2, alpha=255):
            shadow = font.render(text, True, (0, 0, 0))
            shadow.set_alpha(min(180, alpha - 40))
            surface.blit(shadow, (x + shadow_offset, y + shadow_offset))
            main_text = font.render(text, True, color)
            main_text.set_alpha(alpha)
            surface.blit(main_text, (x, y))

        self._draw_hud_score(surface, font_score, font_small, draw_text_shadow)
        self._draw_hud_health(surface, font_small)
        self._draw_hud_powerup(surface, font_small)
        self._draw_hud_progress(surface, font_small)
        self._draw_hud_combo(surface, font_combo_big, font_small)
        self._draw_hud_flash(surface)
        self._draw_hud_pause(surface)

    def _draw_hud_score(self, surface, font_score, font_small, draw_text_shadow):
        """Disegna score e wave number"""
        score_x, score_y = 20, 15
        score_text = f"{self.score:,}"
        draw_text_shadow(score_text, font_score, score_x, score_y, (255, 255, 255), shadow_offset=2)

        wave_y = score_y + 50
        wave_text = f"Wave {self.wave}"
        draw_text_shadow(wave_text, font_small, score_x, wave_y, (180, 180, 180), shadow_offset=1)

    def _draw_hud_health(self, surface, font_small):
        """Disegna i pallini HP"""
        hp_start_x = 1120
        hp_y = 25
        hp_radius = 10
        hp_spacing = 28

        # Label
        hp_label = font_small.render("HP", True, (200, 200, 200))
        surface.blit(hp_label, (hp_start_x - 40, hp_y - 3))

        # Pallini
        for i in range(self.max_health):
            circle_x = hp_start_x + i * hp_spacing
            circle_y = hp_y

            if i < self.health:
                # Pieno
                pygame.draw.circle(surface, (255, 60, 60), (circle_x, circle_y), hp_radius)
                pygame.draw.circle(surface, (255, 140, 140), (circle_x - 2, circle_y - 2), hp_radius // 2)
                pygame.draw.circle(surface, (180, 40, 40), (circle_x, circle_y), hp_radius, 2)
            else:
                # Vuoto
                pygame.draw.circle(surface, (40, 20, 20), (circle_x, circle_y), hp_radius)
                pygame.draw.circle(surface, (80, 40, 40), (circle_x, circle_y), hp_radius, 1)

    def _draw_hud_powerup(self, surface, font_small):
        """Disegna il powerup attivo"""
        if not self.active_powerup:
            return

        powerup_colors = {
            'shotgun': (220, 200, 80),
            'laser': (80, 200, 220),
            'grenade': (220, 140, 80)
        }
        pu_color = powerup_colors.get(self.active_powerup, (180, 180, 180))

        pu_text = f"{self.active_powerup.upper()}"
        ammo_text = f"×{self.powerup_ammo}"

        pu_w = 140
        pu_h = 28
        pu_x = 640 - pu_w // 2
        pu_y = 18

        # Background trasparente
        bg_surf = pygame.Surface((pu_w, pu_h), pygame.SRCALPHA)
        bg_surf.fill((25, 25, 30, 120))
        surface.blit(bg_surf, (pu_x, pu_y))

        # Bordo colorato
        border_surf = pygame.Surface((pu_w, pu_h), pygame.SRCALPHA)
        pygame.draw.rect(border_surf, pu_color + (150,), (0, 0, pu_w, pu_h), 1)
        surface.blit(border_surf, (pu_x, pu_y))

        # Accent line
        accent_surf = pygame.Surface((pu_w, 2), pygame.SRCALPHA)
        accent_surf.fill(pu_color + (180,))
        surface.blit(accent_surf, (pu_x, pu_y))

        # Testo centrato verticalmente
        text_surf = font_small.render(pu_text, True, (255, 255, 255))
        text_surf.set_alpha(160)
        text_h = text_surf.get_height()
        text_x = pu_x + 10
        text_y = pu_y + (pu_h - text_h) // 2
        surface.blit(text_surf, (text_x, text_y))

        # Munizioni
        ammo_surf = font_small.render(ammo_text, True, pu_color)
        ammo_surf.set_alpha(200)
        ammo_h = ammo_surf.get_height()
        ammo_x = pu_x + pu_w - ammo_surf.get_width() - 10
        ammo_y = pu_y + (pu_h - ammo_h) // 2
        surface.blit(ammo_surf, (ammo_x, ammo_y))

    def _draw_hud_progress(self, surface, font_small):
        """Disegna la barra progress wave"""
        progress_w = 200
        progress_h = 5
        progress_x = 640 - progress_w // 2
        progress_y = 695

        progress = min(1.0, self.missiles_destroyed_this_wave / self.missiles_needed_for_wave)

        # Background
        pygame.draw.rect(surface, (40, 40, 50), (progress_x, progress_y, progress_w, progress_h))

        # Fill
        if progress > 0:
            fill_w = int(progress_w * progress)
            pygame.draw.rect(surface, (100, 180, 255), (progress_x, progress_y, fill_w, progress_h))
            if fill_w > 2:
                pygame.draw.rect(surface, (160, 220, 255), (progress_x, progress_y, fill_w, 1))

        # Bordo
        pygame.draw.rect(surface, (80, 80, 90), (progress_x, progress_y, progress_w, progress_h), 1)

        # Counter
        prog_text = f"{self.missiles_destroyed_this_wave}/{self.missiles_needed_for_wave}"
        prog_label = font_small.render(prog_text, True, (140, 140, 140))
        prog_label_w = prog_label.get_width()
        surface.blit(prog_label, (640 - prog_label_w // 2, progress_y + 8))

    def _draw_hud_combo(self, surface, font_combo_big, font_small):
        """Disegna il sistema combo"""
        if self.combo == 0:
            return

        combo_base_x = 1140
        combo_base_y = 60

        # Determina livello
        if self.combo >= 15:
            combo_color = (200, 100, 255)
            combo_label = "INSANE"
            combo_glow = (255, 150, 255)
        elif self.combo >= 10:
            combo_color = (255, 100, 100)
            combo_label = "BRUTAL"
            combo_glow = (255, 150, 150)
        elif self.combo >= 5:
            combo_color = (255, 180, 80)
            combo_label = "GREAT"
            combo_glow = (255, 220, 150)
        else:
            combo_color = (255, 255, 120)
            combo_label = "COMBO"
            combo_glow = (255, 255, 200)

        # Container
        combo_container_w = 120
        combo_container_h = 80
        combo_container_x = combo_base_x - 10
        combo_container_y = combo_base_y - 10

        container_surf = pygame.Surface((combo_container_w, combo_container_h), pygame.SRCALPHA)
        container_surf.fill((20, 20, 25, 100))
        surface.blit(container_surf, (combo_container_x, combo_container_y))

        # Bordo
        border_surf = pygame.Surface((combo_container_w, combo_container_h), pygame.SRCALPHA)
        pygame.draw.rect(border_surf, combo_color + (120,), (0, 0, combo_container_w, combo_container_h), 2)
        surface.blit(border_surf, (combo_container_x, combo_container_y))

        # Label
        label_font = pygame.font.Font(None, 20)
        label_surf = label_font.render(combo_label, True, combo_color)
        label_surf.set_alpha(220)
        label_w = label_surf.get_width()
        surface.blit(label_surf, (combo_base_x + 45 - label_w // 2, combo_base_y))

        # Numero con glow
        combo_text = f"×{self.combo}"
        combo_num_surf = font_combo_big.render(combo_text, True, combo_glow)
        combo_num_surf.set_alpha(240)
        combo_num_w = combo_num_surf.get_width()
        surface.blit(combo_num_surf, (combo_base_x + 45 - combo_num_w // 2, combo_base_y + 18))

        combo_main_surf = font_combo_big.render(combo_text, True, combo_color)
        surface.blit(combo_main_surf, (combo_base_x + 45 - combo_num_w // 2, combo_base_y + 18))

        # Timer bar
        timer_w = 100
        timer_h = 6
        timer_x = combo_base_x
        timer_y = combo_base_y + 60

        timer_ratio = self.combo_timer / self.combo_decay_time
        timer_fill_w = int(timer_w * timer_ratio)

        pygame.draw.rect(surface, (30, 30, 40), (timer_x, timer_y, timer_w, timer_h))

        if timer_fill_w > 0:
            pygame.draw.rect(surface, combo_color, (timer_x, timer_y, timer_fill_w, timer_h))
            pygame.draw.rect(surface, combo_glow, (timer_x, timer_y, timer_fill_w, 2))

            # Warning flash
            if timer_ratio < 0.3:
                flash_alpha = int(100 * (1 - timer_ratio / 0.3))
                flash_surf = pygame.Surface((timer_fill_w, timer_h), pygame.SRCALPHA)
                flash_surf.fill((255, 255, 255, flash_alpha))
                surface.blit(flash_surf, (timer_x, timer_y))

        pygame.draw.rect(surface, (120, 120, 130), (timer_x, timer_y, timer_w, timer_h), 1)

    def _draw_hud_flash(self, surface):
        """Disegna il flash dello schermo"""
        if self.screen_flash > 0:
            flash_alpha = min(50, int(self.screen_flash * 40))
            flash_surf = pygame.Surface((1280, 720), pygame.SRCALPHA)
            flash_surf.fill((255, 255, 255, flash_alpha))
            surface.blit(flash_surf, (0, 0))

    def _draw_hud_pause(self, surface):
        """Disegna il menu di pausa"""
        if not (self.paused and self.confirm_exit):
            return

        # Overlay
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        # Container
        pause_w, pause_h = 420, 220
        pause_x = 640 - pause_w // 2
        pause_y = 250

        pygame.draw.rect(surface, (25, 25, 30), (pause_x, pause_y, pause_w, pause_h))
        pygame.draw.rect(surface, (100, 100, 110), (pause_x, pause_y, pause_w, pause_h), 2)
        pygame.draw.rect(surface, (100, 180, 255), (pause_x, pause_y, pause_w, 3))

        # Titolo
        pause_font = pygame.font.Font(None, 64)
        pause_text = pause_font.render("PAUSED", True, (255, 255, 255))
        pause_text_w = pause_text.get_width()
        surface.blit(pause_text, (640 - pause_text_w // 2, pause_y + 35))

        # Separatore
        sep_x = pause_x + 40
        sep_w = pause_w - 80
        pygame.draw.line(surface, (60, 60, 70), (sep_x, pause_y + 105), (sep_x + sep_w, pause_y + 105), 1)

        # Opzioni
        opt_font = pygame.font.Font(None, 28)

        exit_icon = opt_font.render("◀", True, (255, 100, 100))
        exit_text = opt_font.render("LEFT CLICK", True, (255, 100, 100))
        exit_label = opt_font.render("Exit Game", True, (200, 200, 200))
        surface.blit(exit_icon, (pause_x + 30, pause_y + 125))
        surface.blit(exit_text, (pause_x + 55, pause_y + 125))
        surface.blit(exit_label, (pause_x + 190, pause_y + 125))

        cont_icon = opt_font.render("▶", True, (100, 255, 100))
        cont_text = opt_font.render("RIGHT CLICK", True, (100, 255, 100))
        cont_label = opt_font.render("Continue", True, (200, 200, 200))
        surface.blit(cont_icon, (pause_x + 30, pause_y + 165))
        surface.blit(cont_text, (pause_x + 55, pause_y + 165))
        surface.blit(cont_label, (pause_x + 210, pause_y + 165))


    def draw_heart(self, surface, x, y, color, size, filled=True):
        points = [
            (x, y + size // 3),
            (x - size, y - size // 2),
            (x - size // 2, y - size),
            (x, y - size // 2),
            (x + size // 2, y - size),
            (x + size, y - size // 2),
        ]
        if filled:
            pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, color, points, 3)

    def get_daily_stats(self) -> Dict[str, any]:
        """FONDAMENTALE: Ritorna statistiche per schermata high score"""
        return {
            'Final Score': self.score,
            'Max Combo': f"x{self.max_combo}",
            'Wave Reached': self.wave,
            'Accuracy': f"{self.accuracy}%"
        }












class SpinnerDefense(MiniGame):
    def __init__(self, synth: SoundSynthesizer):
        super().__init__()
        self.synth = synth

        # Core game state
        self.rotation = 0
        self.enemies = []
        self.spawn_timer = 0
        self.lives = 3
        self.max_lives = 5
        self.level = 1
        self.wave = 1

        # Combo system
        self.combo = 0
        self.combo_timer = 0
        self.combo_max = 0
        self.last_hit_time = 0
        self.combo_multiplier = 1.0

        # Visual effects
        self.particles = []
        self.screen_shake = 0
        self.flash_timer = 0
        self.time = 0
        self.bullets = []
        self.bullet_time = 1.0
        self.bullet_time_timer = 0

        # Backgrounds and animations
        self.stars = []
        self.explosions = []
        self.floating_texts = []
        self.speed_lines = []
        self.power_ups = []

        # Power-ups
        self.power_up_spawn_timer = 0
        self.shield_active = False
        self.shield_power = 0
        self.shield_rotation = 0
        self.shotgun_ammo = 0
        self.uzi_ammo = 0
        self.auto_fire_delay = 0
        self.multishot_ammo = 0
        self.pierce_ammo = 0

        # Enemy types
        self.enemy_types = {
            'basic': {'health': 1, 'speed': 80, 'points': 10, 'color': (255, 100, 100), 'size': 10},
            'fast': {'health': 1, 'speed': 140, 'points': 25, 'color': (255, 200, 80), 'size': 8},
            'tank': {'health': 2, 'speed': 50, 'points': 40, 'color': (200, 100, 255), 'size': 14},
            'zigzag': {'health': 1, 'speed': 100, 'points': 30, 'color': (100, 255, 180), 'size': 11},
            'swirl': {'health': 1, 'speed': 90, 'points': 35, 'color': (255, 150, 255), 'size': 9}
        }

        # Fonts
        self.font_huge = None
        self.font_big = None
        self.font_medium = None
        self.font_small = None
        self.font_tiny = None

        # Animation timers
        self.player_pulse = 0
        self.player_rotation = 0
        self.weapon_charge = 0
        self.hit_flash = 0
        self.rotation_speed = 0
        self.barrel_recoil = 0

        # Level progression
        self.enemies_killed_this_wave = 0
        self.enemies_needed_for_wave = 8
        self.wave_complete_timer = 0

        # Statistics
        self.total_shots = 0
        self.total_hits = 0
        self.accuracy = 0

        # Arcade effects
        self.camera_shake_x = 0
        self.camera_shake_y = 0
        self.time_slow = 1.0
        self.perfect_shot_streak = 0

        self.reset()

    def get_name(self) -> str:
        return "Spinner Defense"

    def get_description(self) -> str:
        return "Epic spinner combat with combos & levels!"

    def reset(self):
        self.score = 0
        self.game_over = False
        self.rotation = 0
        self.enemies = []
        self.paused = False
        self.spawn_timer = 1.0
        self.lives = 3
        self.level = 1
        self.wave = 1
        self.combo = 0
        self.combo_timer = 0
        self.combo_max = 0
        self.last_hit_time = 0
        self.combo_multiplier = 1.0
        self.particles = []
        self.explosions = []
        self.floating_texts = []
        self.bullets = []
        self.power_ups = []
        self.screen_shake = 0
        self.flash_timer = 0
        self.time = 0
        self.power_up_spawn_timer = 8.0
        self.shield_active = False
        self.shield_power = 0
        self.shield_rotation = 0
        self.shotgun_ammo = 0
        self.uzi_ammo = 0
        self.auto_fire_delay = 0
        self.multishot_ammo = 0
        self.pierce_ammo = 0
        self.player_pulse = 0
        self.player_rotation = 0
        self.weapon_charge = 0
        self.hit_flash = 0
        self.rotation_speed = 0
        self.barrel_recoil = 0
        self.enemies_killed_this_wave = 0
        self.enemies_needed_for_wave = 8
        self.wave_complete_timer = 0
        self.total_shots = 0
        self.total_hits = 0
        self.accuracy = 0
        self.camera_shake_x = 0
        self.camera_shake_y = 0
        self.time_slow = 1.0
        self.bullet_time = 1.0
        self.bullet_time_timer = 0
        self.perfect_shot_streak = 0

        # Initialize fonts
        self.font_huge = pygame.font.Font(None, 100)
        self.font_big = pygame.font.Font(None, 60)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 28)
        self.font_tiny = pygame.font.Font(None, 20)

        # Create star background
        self.stars = []
        for _ in range(200):
            self.stars.append({
                'x': random.randint(0, 1280),
                'y': random.randint(0, 720),
                'speed': random.uniform(0.5, 4.0),
                'size': random.randint(1, 3),
                'brightness': random.uniform(0.3, 1.0),
                'pulse_offset': random.uniform(0, math.pi * 2),
                'layer': random.randint(1, 3)
            })

        # Create speed lines
        self.speed_lines = []
        for _ in range(35):
            self.speed_lines.append({
                'x': random.randint(-100, 1380),
                'y': random.randint(0, 720),
                'speed': random.uniform(12, 30),
                'length': random.randint(50, 150),
                'thickness': random.randint(1, 2),
                'alpha': random.randint(60, 140)
            })





    def update(self, dt: float, spinner_delta: float, spinner: SpinnerInput) -> bool:
        # === MENU PAUSA IDENTICO A MISSILE COMMANDER ===
        if spinner.is_right_clicked():
            if not hasattr(self, 'paused') or not self.paused:
                self.paused = True
                self.confirmexit = True
                self.synth.create_blip(0).play()
            else:
                self.paused = False
                self.confirmexit = False
                self.synth.create_select().play()
        
        if spinner.is_left_clicked() and hasattr(self, 'paused') and self.paused:
            self.synth.create_back().play()
            self.game_over = True
            return False
        
        # Blocca gameplay se in pausa
        if hasattr(self, 'paused') and self.paused:
            return True
        # === FINE PAUSA ===
        
        if self.game_over:
            self._update_game_over(dt, spinner)
            return not spinner.is_right_clicked()

        # Apply time effects
        effective_dt = dt * self.time_slow

        # Update bullet time
        if self.bullet_time_timer > 0:
            self.bullet_time_timer -= dt
            self.time_slow = 0.5
            if self.bullet_time_timer <= 0:
                self.time_slow = 1.0
        else:
            self.time_slow = 1.0

        # Update time and animations
        self.time += dt
        self.player_pulse += dt * 4
        self.player_rotation += dt * 2
        self.weapon_charge += dt * 8
        self.shield_rotation += dt * 3

        # Barrel recoil
        if self.barrel_recoil > 0:
            self.barrel_recoil -= dt * 15
            self.barrel_recoil = max(0, self.barrel_recoil)

        # Update rotation with smooth acceleration
        target_rotation_speed = spinner_delta
        self.rotation_speed += (target_rotation_speed - self.rotation_speed) * 0.3
        self.rotation += self.rotation_speed
        self.rotation = self.rotation % 360

        # Update combo timer
        if self.combo > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                if self.combo >= 5:
                    self._add_floating_text(640, 200, f"Combo Lost x{self.combo}", (255, 120, 120), 0.6)
                self.combo = 0
                self.combo_multiplier = 1.0
                self.perfect_shot_streak = 0

        # Update auto fire delay
        if self.auto_fire_delay > 0:
            self.auto_fire_delay -= dt

        # Update visual effects
        self._update_background(effective_dt)
        self._update_particles(effective_dt)
        self._update_bullets(effective_dt)
        self._update_floating_texts(dt)
        self._update_power_ups(effective_dt)

        # Camera shake
        if self.screen_shake > 0:
            self.screen_shake -= dt * 6
            self.screen_shake = max(0, self.screen_shake)
            intensity = self.screen_shake * 15
            self.camera_shake_x = random.uniform(-intensity, intensity)
            self.camera_shake_y = random.uniform(-intensity, intensity)
        else:
            self.camera_shake_x *= 0.8
            self.camera_shake_y *= 0.8

        if self.flash_timer > 0:
            self.flash_timer -= dt * 4

        if self.hit_flash > 0:
            self.hit_flash -= dt * 6

        # Wave completion check
        if self.wave_complete_timer > 0:
            self.wave_complete_timer -= dt
            if self.wave_complete_timer <= 0:
                self._start_new_wave()
            return True

        # Spawn power-ups
        self.power_up_spawn_timer -= dt
        if self.power_up_spawn_timer <= 0:
            self._spawn_power_up()
            self.power_up_spawn_timer = random.uniform(10, 16)

        # Spawn enemies
        self._spawn_enemies(effective_dt)

        # Update enemies
        self._update_enemies(effective_dt)

        # Handle shooting
        if spinner.is_left_clicked():
            self._handle_shoot()
        elif spinner.is_left_pressed() and self.uzi_ammo > 0 and self.auto_fire_delay <= 0:
            self._handle_shoot()
            self.auto_fire_delay = 0.06

        return True  # Cambiato per pausa system










    def _update_background(self, dt: float):
        for star in self.stars:
            star['x'] -= star['speed'] * dt * 25 * star['layer']
            if star['x'] < -10:
                star['x'] = 1290
                star['y'] = random.randint(0, 720)

        speed_multiplier = 1.0 + (self.combo * 0.1)
        for line in self.speed_lines:
            line['x'] -= line['speed'] * dt * 100 * speed_multiplier
            if line['x'] + line['length'] < 0:
                line['x'] = 1280 + random.randint(0, 200)
                line['y'] = random.randint(0, 720)
                line['speed'] = random.uniform(12, 30)

    def _spawn_power_up(self):
        angle = random.uniform(0, 360)
        rad = math.radians(angle)
        spawn_distance = 550

        rand = random.random()
        if rand < 0.20 and self.lives < self.max_lives:
            pu_type = 'LIFE'
            color = (255, 100, 255)
        elif rand < 0.35:
            pu_type = 'SHOTGUN'
            color = (255, 220, 80)
        elif rand < 0.50:
            pu_type = 'UZI'
            color = (80, 255, 220)
        elif rand < 0.65:
            pu_type = 'SHIELD'
            color = (120, 220, 255)
        elif rand < 0.80:
            pu_type = 'TRIPLE'
            color = (255, 180, 100)
        else:
            pu_type = 'PIERCE'
            color = (180, 100, 255)

        self.power_ups.append({
            'x': 640 + math.cos(rad) * spawn_distance,
            'y': 360 + math.sin(rad) * spawn_distance,
            'angle': angle,
            'type': pu_type,
            'color': color,
            'pulse': 0,
            'rotation': 0,
            'lifetime': 15.0,
            'collected': False,
            'spawn_anim': 1.0
        })




    def _update_power_ups(self, dt: float):
        for pu in self.power_ups[:]:
            if pu['collected']:
                continue

            # Animations
            pu['pulse'] += dt * 6
            pu['rotation'] += dt * 2

            # Spawn animation
            if pu['spawn_anim'] > 0:
                pu['spawn_anim'] -= dt * 2
                pu['spawn_anim'] = max(0, pu['spawn_anim'])

            pu['lifetime'] -= dt

            if pu['lifetime'] <= 0:
                # Fade out animation
                for _ in range(15):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(50, 150)
                    self._add_particle(pu['x'], pu['y'], pu['color'],
                                    vx=math.cos(angle) * speed,
                                    vy=math.sin(angle) * speed,
                                    size=3, life=0.5, gravity=False)
                self.power_ups.remove(pu)
                continue

            # Drift verso centro
            rad = math.radians(pu['angle'])
            pu['x'] -= math.cos(rad) * 25 * dt
            pu['y'] -= math.sin(rad) * 25 * dt

            # Trail particles
            if random.random() < 0.3:
                self._add_particle(pu['x'], pu['y'], pu['color'], 
                                size=2, life=0.4, gravity=False)

            # COLLISION CON PROIETTILI (non più con player)
            for bullet in self.bullets[:]:
                dist = math.sqrt((pu['x'] - bullet['x'])**2 + (pu['y'] - bullet['y'])**2)
                if dist < 30:  # Raggio di collisione powerup
                    self._collect_power_up(pu)
                    pu['collected'] = True
                    self.power_ups.remove(pu)
                    # Rimuovi anche il proiettile che ha colpito il powerup
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break



    def _collect_power_up(self, pu):
        self.synth.create_high_score().play()
        self._add_explosion(pu['x'], pu['y'], pu['color'], 35)
        self.screen_shake = 0.6

        # Ring explosion effect
        for i in range(20):
            angle = (i / 20) * 2 * math.pi
            speed = 200
            self._add_particle(pu['x'], pu['y'], pu['color'],
                             vx=math.cos(angle) * speed,
                             vy=math.sin(angle) * speed,
                             size=4, life=0.6, gravity=False)

        if pu['type'] == 'LIFE':
            if self.lives < self.max_lives:
                self.lives += 1
                self._add_floating_text(640, 360, "+1 LIFE", (255, 120, 255), 1.5)
                self.score += 100
        elif pu['type'] == 'SHOTGUN':
            self.shotgun_ammo = 15
            self._add_floating_text(640, 360, "SHOTGUN", (255, 220, 80), 1.2)
        elif pu['type'] == 'UZI':
            self.uzi_ammo = 80
            self._add_floating_text(640, 360, "AUTO RIFLE", (80, 255, 220), 1.2)
        elif pu['type'] == 'SHIELD':
            self.shield_active = True
            self.shield_power = 4
            self._add_floating_text(640, 360, "SHIELD", (120, 220, 255), 1.2)
        elif pu['type'] == 'TRIPLE':
            self.multishot_ammo = 20
            self._add_floating_text(640, 360, "TRIPLE SHOT", (255, 180, 100), 1.2)
        elif pu['type'] == 'PIERCE':
            self.pierce_ammo = 25
            self._add_floating_text(640, 360, "PIERCE", (180, 100, 255), 1.2)

    def _spawn_enemies(self, dt: float):
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            enemy_type = self._get_random_enemy_type()
            angle = random.uniform(0, 360)

            max_attempts = 8
            for attempt in range(max_attempts):
                rad = math.radians(angle)
                spawn_distance = 650
                new_x = 640 + math.cos(rad) * spawn_distance
                new_y = 360 + math.sin(rad) * spawn_distance

                too_close = False
                min_distance = 80

                for enemy in self.enemies:
                    dist = math.sqrt((enemy['x'] - new_x)**2 + (enemy['y'] - new_y)**2)
                    if dist < min_distance:
                        too_close = True
                        break

                # Check power-ups distance
                for pu in self.power_ups:
                    if not pu['collected']:
                        dist = math.sqrt((pu['x'] - new_x)**2 + (pu['y'] - new_y)**2)
                        if dist < 100:
                            too_close = True
                            break

                if not too_close:
                    enemy_data = self.enemy_types[enemy_type].copy()
                    self.enemies.append({
                        'x': new_x,
                        'y': new_y,
                        'angle': angle,
                        'type': enemy_type,
                        'health': enemy_data['health'],
                        'max_health': enemy_data['health'],
                        'speed': enemy_data['speed'] * (1 + self.level * 0.05),
                        'points': enemy_data['points'],
                        'color': enemy_data['color'],
                        'size': enemy_data['size'],
                        'hit_flash': 0,
                        'spawn_anim': 1.0,
                        'zigzag_offset': random.uniform(0, math.pi * 2),
                        'zigzag_time': 0,
                        'swirl_angle': 0,
                        'rotation': 0
                    })
                    break

                angle = random.uniform(0, 360)

            base_spawn_time = max(0.4, 1.8 - self.level * 0.05 - self.wave * 0.03)
            self.spawn_timer = base_spawn_time * random.uniform(0.8, 1.3)

    def _get_random_enemy_type(self) -> str:
        if self.level < 2:
            choices = ['basic'] * 80 + ['fast'] * 20
        elif self.level < 4:
            choices = ['basic'] * 60 + ['fast'] * 25 + ['zigzag'] * 15
        elif self.level < 6:
            choices = ['basic'] * 50 + ['fast'] * 25 + ['zigzag'] * 15 + ['swirl'] * 10
        elif self.level < 9:
            choices = ['basic'] * 40 + ['fast'] * 25 + ['zigzag'] * 15 + ['tank'] * 10 + ['swirl'] * 10
        else:
            choices = ['basic'] * 35 + ['fast'] * 25 + ['zigzag'] * 15 + ['tank'] * 15 + ['swirl'] * 10

        return random.choice(choices)

    def _update_enemies(self, dt: float):
        for enemy in self.enemies[:]:
            # Animations
            enemy['rotation'] += dt * 3

            if enemy['spawn_anim'] > 0:
                enemy['spawn_anim'] -= dt * 3
                enemy['spawn_anim'] = max(0, enemy['spawn_anim'])

            if enemy['hit_flash'] > 0:
                enemy['hit_flash'] -= dt * 8

            # Movement patterns
            if enemy['type'] == 'zigzag':
                enemy['zigzag_time'] += dt * 5
                zigzag_angle = enemy['angle'] + math.sin(enemy['zigzag_time'] + enemy['zigzag_offset']) * 20
                rad = math.radians(zigzag_angle)
            elif enemy['type'] == 'swirl':
                enemy['swirl_angle'] += dt * 2
                base_rad = math.radians(enemy['angle'])
                swirl_offset = math.sin(enemy['swirl_angle']) * 100
                rad = base_rad
                enemy['x'] -= math.cos(rad) * enemy['speed'] * dt + math.cos(base_rad + math.pi/2) * swirl_offset * dt
                enemy['y'] -= math.sin(rad) * enemy['speed'] * dt + math.sin(base_rad + math.pi/2) * swirl_offset * dt
                continue
            else:
                rad = math.radians(enemy['angle'])

            enemy['x'] -= math.cos(rad) * enemy['speed'] * dt
            enemy['y'] -= math.sin(rad) * enemy['speed'] * dt

            if random.random() < 0.2:
                self._add_particle(enemy['x'], enemy['y'], enemy['color'], size=1.5, life=0.3, gravity=False)

            dist = math.sqrt((enemy['x'] - 640)**2 + (enemy['y'] - 360)**2)

            if dist < 50:
                self.enemies.remove(enemy)

                if self.shield_active and self.shield_power > 0:
                    self.shield_power -= 1
                    self._add_explosion(enemy['x'], enemy['y'], (120, 220, 255), 25)
                    self._add_floating_text(640, 360, "BLOCKED", (120, 220, 255), 0.6)
                    self.synth.create_blip(1).play()
                    if self.shield_power <= 0:
                        self.shield_active = False
                else:
                    self.lives -= 1
                    self._add_explosion(enemy['x'], enemy['y'], (255, 100, 100), 40)
                    self.screen_shake = 1.5
                    self.flash_timer = 0.5
                    self.hit_flash = 1.0
                    self.synth.create_hit().play()
                    self._add_floating_text(640, 280, "DAMAGE", (255, 100, 100), 1.0)

                    self.combo = 0
                    self.combo_multiplier = 1.0
                    self.perfect_shot_streak = 0

                    if self.lives <= 0:
                        self.game_over = True
                        self.synth.create_game_over().play()
                        self._add_floating_text(640, 360, "GAME OVER", (255, 80, 80), 3.0)

    def _handle_shoot(self):
        self.total_shots += 1
        self.weapon_charge = 0
        self.barrel_recoil = 1.0

        if self.multishot_ammo > 0:
            self.multishot_ammo -= 1
            self._shoot_multishot()
        elif self.pierce_ammo > 0:
            self.pierce_ammo -= 1
            self._shoot_pierce()
        elif self.shotgun_ammo > 0:
            self.shotgun_ammo -= 1
            self._shoot_shotgun()
        elif self.uzi_ammo > 0:
            self.uzi_ammo -= 1
            self._shoot_single(spread=3, color=(80, 255, 220))
        else:
            self._shoot_single()

    def _shoot_single(self, spread=0, color=(255, 255, 180)):
        rad = math.radians(self.rotation + random.uniform(-spread, spread))
        self.bullets.append({
            'x': 640 + math.cos(rad) * 40,
            'y': 360 + math.sin(rad) * 40,
            'vx': math.cos(rad) * 900,
            'vy': math.sin(rad) * 900,
            'life': 1.8,
            'size': 5,
            'color': color,
            'pierce': False,
            'rotation': 0
        })

        self._create_muzzle_flash(rad, color, 8)

    def _shoot_shotgun(self):
        for i in range(7):
            spread = (i - 3) * 7
            rad = math.radians(self.rotation + spread)
            self.bullets.append({
                'x': 640 + math.cos(rad) * 40,
                'y': 360 + math.sin(rad) * 40,
                'vx': math.cos(rad) * 850,
                'vy': math.sin(rad) * 850,
                'life': 1.4,
                'size': 4,
                'color': (255, 220, 80),
                'pierce': False,
                'rotation': 0
            })

        rad = math.radians(self.rotation)
        self._create_muzzle_flash(rad, (255, 220, 80), 20)
        self.screen_shake = 0.5

    def _shoot_multishot(self):
        for angle_offset in [-25, 0, 25]:
            rad = math.radians(self.rotation + angle_offset)
            self.bullets.append({
                'x': 640 + math.cos(rad) * 40,
                'y': 360 + math.sin(rad) * 40,
                'vx': math.cos(rad) * 900,
                'vy': math.sin(rad) * 900,
                'life': 1.8,
                'size': 5,
                'color': (255, 180, 100),
                'pierce': False,
                'rotation': 0
            })

        rad = math.radians(self.rotation)
        self._create_muzzle_flash(rad, (255, 180, 100), 15)
        self.screen_shake = 0.35

    def _shoot_pierce(self):
        rad = math.radians(self.rotation)
        self.bullets.append({
            'x': 640 + math.cos(rad) * 40,
            'y': 360 + math.sin(rad) * 40,
            'vx': math.cos(rad) * 1100,
            'vy': math.sin(rad) * 1100,
            'life': 2.0,
            'size': 7,
            'color': (180, 100, 255),
            'pierce': True,
            'pierce_count': 0,
            'max_pierce': 5,
            'rotation': 0
        })

        self._create_muzzle_flash(rad, (180, 100, 255), 12)
        self.screen_shake = 0.25

    def _create_muzzle_flash(self, rad, color, count):
        flash_x = 640 + math.cos(rad) * 50
        flash_y = 360 + math.sin(rad) * 50
        for _ in range(count):
            angle = rad + random.uniform(-0.5, 0.5)
            speed = random.uniform(180, 350)
            self._add_particle(flash_x, flash_y, color, 
                             vx=math.cos(angle) * speed,
                             vy=math.sin(angle) * speed,
                             size=random.uniform(3, 6), life=0.25, gravity=False)

    def _update_bullets(self, dt: float):
        for bullet in self.bullets[:]:
            bullet['life'] -= dt
            if bullet['life'] <= 0:
                # Death animation
                for _ in range(5):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(50, 100)
                    self._add_particle(bullet['x'], bullet['y'], bullet['color'],
                                     vx=math.cos(angle) * speed,
                                     vy=math.sin(angle) * speed,
                                     size=2, life=0.2, gravity=False)
                self.bullets.remove(bullet)
                continue

            bullet['rotation'] += dt * 10
            bullet['x'] += bullet['vx'] * dt
            bullet['y'] += bullet['vy'] * dt

            # Trail
            if random.random() < 0.7:
                self._add_particle(bullet['x'], bullet['y'], bullet['color'], 
                                 size=2.5, life=0.2, gravity=False)

            # Collision con nemici (NON con power-ups!)
            hit_enemy = False
            for enemy in self.enemies[:]:
                dist = math.sqrt((enemy['x'] - bullet['x'])**2 + (enemy['y'] - bullet['y'])**2)
                if dist < enemy['size'] + bullet['size']:
                    self.total_hits += 1
                    enemy['health'] -= 1
                    enemy['hit_flash'] = 1.0

                    self._add_explosion(enemy['x'], enemy['y'], (255, 255, 180), 15)

                    for _ in range(8):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(120, 300)
                        self._add_particle(enemy['x'], enemy['y'], (255, 255, 220),
                                         vx=math.cos(angle) * speed,
                                         vy=math.sin(angle) * speed,
                                         size=3, life=0.3, gravity=False)

                    if enemy['health'] <= 0:
                        self._kill_enemy(enemy)

                    if bullet.get('pierce', False):
                        bullet['pierce_count'] = bullet.get('pierce_count', 0) + 1
                        if bullet['pierce_count'] >= bullet.get('max_pierce', 5):
                            hit_enemy = True
                        self.synth.create_score_point().play()
                    else:
                        hit_enemy = True

                    break

            if hit_enemy and bullet in self.bullets:
                self.bullets.remove(bullet)

            if bullet['x'] < -100 or bullet['x'] > 1380 or bullet['y'] < -100 or bullet['y'] > 820:
                self.bullets.remove(bullet)

    def _kill_enemy(self, enemy):
        self.enemies.remove(enemy)

        current_time = self.time
        if current_time - self.last_hit_time < 3.0:
            self.combo += 1
            self.combo_timer = 4.0
            self.perfect_shot_streak += 1
        else:
            self.combo = 1
            self.combo_timer = 4.0
            self.perfect_shot_streak = 1

        self.last_hit_time = current_time
        self.combo_max = max(self.combo_max, self.combo)
        self.combo_multiplier = 1.0 + (self.combo * 0.2)

        if self.perfect_shot_streak >= 10:
            self.combo_multiplier *= 1.5
            if self.perfect_shot_streak == 10:
                self._add_floating_text(640, 300, "PERFECT STREAK", (255, 200, 255), 1.2)
                self.bullet_time_timer = 5.7

        points = int(enemy['points'] * self.combo_multiplier)
        self.score += points

        self._add_explosion(enemy['x'], enemy['y'], enemy['color'], 30)
        self.screen_shake = 0.3

        combo_color = self._get_combo_color()
        if self.combo > 1:
            self._add_floating_text(enemy['x'], enemy['y'], 
                                  f"+{points} COMBO x{self.combo}", combo_color, 0.8)
        else:
            self._add_floating_text(enemy['x'], enemy['y'], f"+{points}", 
                                  (255, 255, 180), 0.6)

        self.synth.create_score_point().play()

        if self.combo == 5:
            self._add_floating_text(640, 250, "COMBO x5", (255, 220, 120), 1.0)
        elif self.combo == 10:
            self._add_floating_text(640, 250, "AMAZING x10", (255, 180, 255), 1.2)
        elif self.combo == 20:
            self._add_floating_text(640, 250, "INCREDIBLE x20", (180, 255, 255), 1.5)

        self.enemies_killed_this_wave += 1
        if self.enemies_killed_this_wave >= self.enemies_needed_for_wave:
            self._complete_wave()

    def _complete_wave(self):
        self.wave_complete_timer = 3.0
        self.wave += 1

        for enemy in self.enemies:
            self._add_explosion(enemy['x'], enemy['y'], enemy['color'], 25)
        self.enemies.clear()

        bonus = self.wave * 200 + self.combo * 50
        self.score += bonus

        self._add_floating_text(640, 300, f"WAVE {self.wave-1} COMPLETE", (180, 255, 180), 2.5)
        self._add_floating_text(640, 360, f"BONUS +{bonus}", (255, 255, 180), 2.0)

        if self.wave % 2 == 0:
            self.level += 1
            self._add_floating_text(640, 420, f"LEVEL {self.level}", (255, 180, 255), 2.0)

            if self.level % 4 == 0 and self.lives < self.max_lives:
                self.lives += 1
                self._add_floating_text(640, 480, "LIFE RESTORED", (255, 120, 255), 1.8)

    def _start_new_wave(self):
        self.enemies_killed_this_wave = 0
        self.enemies_needed_for_wave = int(8 + (self.wave * 1.5))

    def _get_combo_color(self) -> Tuple[int, int, int]:
        if self.combo < 5:
            return (255, 255, 180)
        elif self.combo < 10:
            return (255, 220, 120)
        elif self.combo < 20:
            return (255, 180, 255)
        else:
            return (180, 255, 255)

    def _add_particle(self, x: float, y: float, color: Tuple[int, int, int], 
                     vx: float = None, vy: float = None, size: float = 2, 
                     life: float = 0.4, gravity: bool = True):
        if vx is None:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 90)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

        self.particles.append({
            'x': x,
            'y': y,
            'vx': vx,
            'vy': vy,
            'life': life,
            'max_life': life,
            'color': color,
            'size': size,
            'gravity': gravity
        })

    def _add_explosion(self, x: float, y: float, color: Tuple[int, int, int], count: int = 15):
        for _ in range(count):
            self._add_particle(x, y, color, size=random.uniform(2, 5), life=random.uniform(0.3, 0.7))

    def _add_floating_text(self, x: float, y: float, text: str, color: Tuple[int, int, int], duration: float):
        self.floating_texts.append({
            'x': x,
            'y': y,
            'text': text,
            'color': color,
            'life': duration,
            'max_life': duration,
            'vy': -70,
            'scale': 1.0
        })

    def _update_particles(self, dt: float):
        for particle in self.particles[:]:
            particle['life'] -= dt
            if particle['life'] <= 0:
                self.particles.remove(particle)
                continue

            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt

            if particle['gravity']:
                particle['vy'] += 300 * dt
                particle['vx'] *= 0.97

    def _update_floating_texts(self, dt: float):
        for text in self.floating_texts[:]:
            text['life'] -= dt
            if text['life'] <= 0:
                self.floating_texts.remove(text)
                continue

            text['y'] += text['vy'] * dt
            text['vy'] *= 0.94

            progress = 1.0 - (text['life'] / text['max_life'])
            if progress < 0.15:
                text['scale'] = progress / 0.15
            elif progress > 0.85:
                text['scale'] = 1.0 - ((progress - 0.85) / 0.15)
            else:
                text['scale'] = 1.0 + math.sin(progress * math.pi) * 0.15

    def _update_game_over(self, dt: float, spinner: SpinnerInput):
        self._update_background(dt)
        self._update_particles(dt)
        self._update_bullets(dt)
        self._update_floating_texts(dt)

    def _draw_hexagon(self, surface: pygame.Surface, x: int, y: int, size: float, color: Tuple[int, int, int], rotation: float = 0):
        """Draw hexagon power-up shape"""
        points = []
        for i in range(6):
            angle = math.radians(60 * i + rotation)
            px = x + math.cos(angle) * size
            py = y + math.sin(angle) * size
            points.append((int(px), int(py)))

        # Draw filled hexagon
        pygame.draw.polygon(surface, color, points)

        # Draw outline
        pygame.draw.polygon(surface, (255, 255, 255), points, 3)

        # Inner hexagon
        inner_points = []
        for i in range(6):
            angle = math.radians(60 * i + rotation)
            px = x + math.cos(angle) * (size * 0.6)
            py = y + math.sin(angle) * (size * 0.6)
            inner_points.append((int(px), int(py)))
        pygame.draw.polygon(surface, (255, 255, 255), inner_points, 2)






    def draw(self, surface: pygame.Surface):
        shake_x = int(self.camera_shake_x)
        shake_y = int(self.camera_shake_y)

        # Background gradient dinamico
        for y in range(720):
            factor = y / 720
            wave = math.sin(self.time * 0.4 + factor * 2.5) * 4
            combo_boost = min(20, self.combo * 2)
            r = max(0, min(255, int(2 + wave + combo_boost * 0.2)))
            g = max(0, min(255, int(3 + wave + combo_boost * 0.3)))
            b = max(0, min(255, int(15 + wave + combo_boost * 0.5)))

            if self.time_slow < 1.0:
                b = min(255, b + 30)
                r = max(0, r - 10)

            pygame.draw.line(surface, (r, g, b), (0, y), (1280, y))

        # Stars
        for star in self.stars:
            twinkle = abs(math.sin(self.time * 2 + star['pulse_offset'])) * 0.5 + 0.5
            brightness = int(star['brightness'] * 255 * twinkle)
            color = (brightness, brightness, min(255, brightness + 50))

            x = int(star['x'] + shake_x)
            y = int(star['y'] + shake_y)

            if 0 <= x < 1280 and 0 <= y < 720:
                if star['size'] > 1:
                    pygame.draw.circle(surface, color, (x, y), star['size'])
                    if star['layer'] == 3 and star['size'] > 2:
                        glow = pygame.Surface((star['size'] * 4, star['size'] * 4), pygame.SRCALPHA)
                        pygame.draw.circle(glow, (*color, 50), (star['size'] * 2, star['size'] * 2), star['size'] * 2)
                        surface.blit(glow, (x - star['size'] * 2, y - star['size'] * 2))
                else:
                    try:
                        surface.set_at((x, y), color)
                    except:
                        pass

        # Speed lines
        for line in self.speed_lines:
            alpha = line['alpha']
            if self.combo > 5:
                alpha = min(255, alpha + self.combo * 3)
            color = (70, 90, 160)
            x = int(line['x'] + shake_x)
            y = int(line['y'] + shake_y)

            if -line['length'] <= x < 1280 and 0 <= y < 720:
                line_surf = pygame.Surface((max(1, line['length']), line['thickness'] * 2), pygame.SRCALPHA)
                pygame.draw.line(line_surf, (*color, alpha), (0, line['thickness']), 
                               (line['length'], line['thickness']), line['thickness'])
                surface.blit(line_surf, (x, y))

        center_x = 640 + shake_x
        center_y = 360 + shake_y

        # Shield con rotazione
        if self.shield_active:
            shield_radius = 55
            shield_surf = pygame.Surface((shield_radius * 3, shield_radius * 3), pygame.SRCALPHA)
            center_offset = int(shield_radius * 1.5)

            # Rotating hexagonal shield
            for i in range(3):
                hex_rotation = self.shield_rotation * 60 + i * 120
                self._draw_hexagon(shield_surf, center_offset, center_offset, 
                                 shield_radius - i * 5, (130, 230, 255, 80 - i * 20), hex_rotation)

            surface.blit(shield_surf, (center_x - center_offset, center_y - center_offset))

















        # 1. PARAMETRI E COORDINATE
        # Usa i tuoi centri (es. screen_width // 2)
        center_x, center_y = 640, 360  
        
        # --- FIX ROTAZIONE ---
        # Se il tuo codice di update muove 'rotation', usiamo quella.
        # Se muove 'player_rotation', cambia la riga sotto.
        current_rot = self.rotation 
        rad = math.radians(current_rot)
        
        # Dinamica pulsazione
        pulse = 25 + abs(math.sin(self.player_pulse)) * 8
        pulse_fast = abs(math.sin(self.player_pulse * 3)) 

        # 2. ATMOSFERA ESTERNA (Glow soffuso)
        atmo_size = int(pulse * 4.5)
        atmo_surf = pygame.Surface((atmo_size, atmo_size), pygame.SRCALPHA)
        center_atmo = atmo_size // 2
        for r in range(int(pulse * 2.2), 0, -2):
            dist_norm = r / (pulse * 2.2)
            alpha = int(70 * (1 - dist_norm) ** 2)
            color = (0, 100 + int(100 * (1 - dist_norm)), 255, alpha)
            pygame.draw.circle(atmo_surf, color, (center_atmo, center_atmo), r)
        surface.blit(atmo_surf, (center_x - center_atmo, center_y - center_atmo))

        # 3. SUPERFICIE PIANETA
        planet_diam = int(pulse * 2)
        planet_surf = pygame.Surface((planet_diam, planet_diam), pygame.SRCALPHA)
        for r in range(int(pulse), 0, -1):
            dist_norm = 1 - (r / pulse)
            c_val = int(20 + 60 * (1 - dist_norm))
            color = (c_val, c_val + 20, c_val + 80)
            pygame.draw.circle(planet_surf, color, (int(pulse), int(pulse)), r)

        # 4. CRATERI (Ruotano sincronizzati)
        random.seed(42) 
        for i in range(15):
            # Usiamo current_rot anche qui per coerenza visiva
            angle = (i * 24.5) + (current_rot * 0.1)
            dist = random.uniform(0, pulse * 0.8)
            cx = int(pulse + math.cos(angle) * dist)
            cy = int(pulse + math.sin(angle) * dist)
            pygame.draw.circle(planet_surf, (10, 20, 40), (cx, cy), random.randint(1, 3))
            pygame.draw.circle(planet_surf, (80, 150, 255), (cx, cy), 1)
        surface.blit(planet_surf, (center_x - int(pulse), center_y - int(pulse)))

        # 5. ANELLI ORBITALI
        for i in range(2):
            ring_r = pulse + 10 + i * 6
            ring_color = (0, 200, 255, 40 - i * 20)
            pygame.draw.circle(surface, ring_color, (center_x, center_y), int(ring_r), 2)

        # 6. CANNONE (Weapon Barrel)
        # Sincronizzato con self.rotation e self.weapon_charge
        weapon_charge_offset = math.sin(self.weapon_charge) * 6
        barrel_recoil_offset = self.barrel_recoil * 10
        weapon_length = 45 + weapon_charge_offset - barrel_recoil_offset
        
        barrel_start_dist = pulse + 5
        barrel_end_dist = barrel_start_dist + weapon_length

        # Colore dinamico basato sulle munizioni
        if self.multishot_ammo > 0: weapon_color = (255, 180, 100)
        elif self.pierce_ammo > 0: weapon_color = (180, 100, 255)
        elif self.shotgun_ammo > 0: weapon_color = (255, 220, 80)
        elif self.uzi_ammo > 0: weapon_color = (80, 255, 220)
        else: weapon_color = (0, 255, 180)

        bx_start = center_x + math.cos(rad) * barrel_start_dist
        by_start = center_y + math.sin(rad) * barrel_start_dist
        bx_end = center_x + math.cos(rad) * barrel_end_dist
        by_end = center_y + math.sin(rad) * barrel_end_dist

        # Glow dell'arma
        weapon_glow = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.line(weapon_glow, (*weapon_color, 100), (bx_start, by_start), (bx_end, by_end), 12)
        surface.blit(weapon_glow, (0, 0))

        # Disegno cannone
        pygame.draw.line(surface, weapon_color, (bx_start, by_start), (bx_end, by_end), 6)
        pygame.draw.line(surface, (255, 255, 255), (bx_start, by_start), (bx_end, by_end), 2)
        pygame.draw.circle(surface, (255, 255, 220), (int(bx_end), int(by_end)), 8) # Punta

        # 7. LASER ROSSO SFUMATO (Arcade Style)
        laser_max_len = 600
        steps = 15 
        laser_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        
        for i in range(steps):
            d_start = barrel_end_dist + (laser_max_len / steps) * i
            d_end = barrel_end_dist + (laser_max_len / steps) * (i + 1)
            
            # Alpha che sfuma verso la fine
            alpha = int(180 * (1 - (i / steps))**1.5)
            
            p1 = (center_x + math.cos(rad) * d_start, center_y + math.sin(rad) * d_start)
            p2 = (center_x + math.cos(rad) * d_end, center_y + math.sin(rad) * d_end)
            
            # Disegno strati: Glow largo e Core sottile
            pygame.draw.line(laser_surf, (255, 0, 0, alpha // 3), p1, p2, 8)
            pygame.draw.line(laser_surf, (255, 50, 50, alpha), p1, p2, 3)
            pygame.draw.line(laser_surf, (255, 200, 200, alpha), p1, p2, 1)
            
        surface.blit(laser_surf, (0, 0))

        # 8. MIRINO (CROSSHAIR)
        target_x = center_x + math.cos(rad) * (barrel_end_dist + laser_max_len)
        target_y = center_y + math.sin(rad) * (barrel_end_dist + laser_max_len)
        
        cross_size = 5 + pulse_fast * 3
        pygame.draw.circle(surface, (255, 0, 0, 180), (int(target_x), int(target_y)), int(cross_size), 1)
        pygame.draw.circle(surface, (255, 255, 255, 200), (int(target_x), int(target_y)), 2)
        
        off = cross_size + 2
        pygame.draw.line(surface, (255, 0, 0), (target_x - off, target_y), (target_x + off, target_y), 1)
        pygame.draw.line(surface, (255, 0, 0), (target_x, target_y - off), (target_x, target_y + off), 1)

        # 9. BORDO FINALE (Rim Light)
        pygame.draw.circle(surface, (0, 220, 255), (center_x, center_y), int(pulse), 2)


























        # Bullets
        for bullet in self.bullets:
            x = int(bullet['x'] + shake_x)
            y = int(bullet['y'] + shake_y)

            # Rotating bullet
            bullet_surf = pygame.Surface((int(bullet['size'] * 8), int(bullet['size'] * 8)), pygame.SRCALPHA)
            center_b = int(bullet['size'] * 4)

            # Glow
            pygame.draw.circle(bullet_surf, (*bullet['color'], 120), (center_b, center_b), int(bullet['size'] * 3))

            # Core
            pygame.draw.circle(bullet_surf, bullet['color'], (center_b, center_b), int(bullet['size']))
            pygame.draw.circle(bullet_surf, (255, 255, 255), (center_b, center_b), int(bullet['size']), 1)

            # Rotation indicator
            rot_angle = math.radians(bullet['rotation'] * 36)
            rot_x = center_b + math.cos(rot_angle) * (bullet['size'] - 2)
            rot_y = center_b + math.sin(rot_angle) * (bullet['size'] - 2)
            pygame.draw.circle(bullet_surf, (255, 255, 255), (int(rot_x), int(rot_y)), 2)

            if bullet.get('pierce', False):
                pygame.draw.circle(bullet_surf, (255, 255, 255), (center_b, center_b), int(bullet['size']) + 3, 2)

            surface.blit(bullet_surf, (x - center_b, y - center_b))

        # Particles
        for particle in self.particles:
            alpha_factor = particle['life'] / particle['max_life']
            size = particle['size'] * alpha_factor

            if size > 0.5:
                x = int(particle['x'] + shake_x)
                y = int(particle['y'] + shake_y)

                if -50 <= x < 1330 and -50 <= y < 770:
                    glow_surf = pygame.Surface((int(size * 4), int(size * 4)), pygame.SRCALPHA)
                    color_alpha = (*particle['color'], int(100 * alpha_factor))
                    pygame.draw.circle(glow_surf, color_alpha, (int(size * 2), int(size * 2)), int(size * 2))
                    surface.blit(glow_surf, (x - int(size * 2), y - int(size * 2)))

                    pygame.draw.circle(surface, particle['color'], (x, y), max(1, int(size)))

        # Enemies con animazioni migliorate
        for enemy in self.enemies:
            x = int(enemy['x'] + shake_x)
            y = int(enemy['y'] + shake_y)

            spawn_scale = max(0.1, 1.0 - enemy['spawn_anim'] * 0.5)
            size = int(enemy['size'] * spawn_scale)

            if size < 1:
                continue

            color = enemy['color']
            if enemy['hit_flash'] > 0:
                flash = int(140 * enemy['hit_flash'])
                color = tuple(min(255, c + flash) for c in color)

            # Glow pulsante
            glow_pulse = abs(math.sin(self.time * 3 + enemy['rotation'])) * 0.3 + 0.7
            glow_surf = pygame.Surface((size * 6, size * 6), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*color, int(80 * glow_pulse)), (size * 3, size * 3), size * 3)
            surface.blit(glow_surf, (x - size * 3, y - size * 3))

            # Body
            pygame.draw.circle(surface, color, (x, y), size)
            pygame.draw.circle(surface, (255, 255, 255), (x, y), size, 2)

            # Type indicators
            if enemy['type'] == 'tank':
                pygame.draw.circle(surface, (120, 50, 180), (x, y), max(1, size - 4))
                pygame.draw.circle(surface, color, (x, y), max(1, size - 8))
                pygame.draw.circle(surface, (255, 255, 255), (x, y), max(1, size - 8), 1)
            elif enemy['type'] == 'fast':
                # Speed indicators
                for i in range(3):
                    line_angle = math.radians(enemy['rotation'] * 36 + i * 120)
                    lx1 = x + math.cos(line_angle) * (size - 6)
                    ly1 = y + math.sin(line_angle) * (size - 6)
                    lx2 = x + math.cos(line_angle) * (size - 3)
                    ly2 = y + math.sin(line_angle) * (size - 3)
                    pygame.draw.line(surface, (255, 255, 200), (int(lx1), int(ly1)), (int(lx2), int(ly2)), 2)
            elif enemy['type'] == 'zigzag':
                pygame.draw.circle(surface, (20, 220, 120), (x, y), max(1, size - 4))
                # Zigzag pattern
                for i in range(4):
                    dot_angle = math.radians(i * 90 + enemy['rotation'] * 36)
                    dot_x = x + math.cos(dot_angle) * (size - 6)
                    dot_y = y + math.sin(dot_angle) * (size - 6)
                    pygame.draw.circle(surface, (200, 255, 220), (int(dot_x), int(dot_y)), 2)
            elif enemy['type'] == 'swirl':
                pygame.draw.circle(surface, (220, 100, 220), (x, y), max(1, size - 3))
                for angle in [0, 120, 240]:
                    rad = math.radians(angle + enemy['swirl_angle'] * 50)
                    px = x + math.cos(rad) * (size - 5)
                    py = y + math.sin(rad) * (size - 5)
                    pygame.draw.circle(surface, (255, 200, 255), (int(px), int(py)), 3)
                    pygame.draw.circle(surface, (255, 255, 255), (int(px), int(py)), 3, 1)

            # Health bar
            if enemy['max_health'] > 1:
                bar_w = size * 2.5
                bar_h = 4
                bar_x = x - bar_w // 2
                bar_y = y - size - 12

                pygame.draw.rect(surface, (40, 40, 40), (int(bar_x), int(bar_y), int(bar_w), bar_h))
                health_ratio = enemy['health'] / enemy['max_health']
                health_w = int(bar_w * health_ratio)
                health_col = (0, 255, 100) if health_ratio > 0.5 else (255, 220, 0) if health_ratio > 0.33 else (255, 80, 80)
                pygame.draw.rect(surface, health_col, (int(bar_x), int(bar_y), health_w, bar_h))
                pygame.draw.rect(surface, (200, 200, 200), (int(bar_x), int(bar_y), int(bar_w), bar_h), 1)

        # HEXAGONAL POWER-UPS
        for pu in self.power_ups:
            if pu.get('collected', False):
                continue

            x = int(pu['x'] + shake_x)
            y = int(pu['y'] + shake_y)

            # Spawn animation
            spawn_scale = 1.0 - pu['spawn_anim'] * 0.5
            pulse_size = (26 + abs(math.sin(pu['pulse'])) * 6) * spawn_scale
            hex_rotation = pu['rotation'] * 60

            # Outer glow
            glow = pygame.Surface((int(pulse_size * 5), int(pulse_size * 5)), pygame.SRCALPHA)
            glow_center = int(pulse_size * 2.5)
            pygame.draw.circle(glow, (*pu['color'], 100), (glow_center, glow_center), int(pulse_size * 2))
            surface.blit(glow, (x - glow_center, y - glow_center))

            # Hexagonal shape
            self._draw_hexagon(surface, x, y, pulse_size, pu['color'], hex_rotation)

            # Text label
            label_surf = self.font_tiny.render(pu['type'], True, (255, 255, 255))
            label_surf.set_alpha(220)
            surface.blit(label_surf, (x - label_surf.get_width() // 2, y - label_surf.get_height() // 2))

            # Lifetime warning
            if pu['lifetime'] < 5:
                warning_alpha = int((math.sin(self.time * 12) * 0.5 + 0.5) * 255)
                warning_surf = pygame.Surface((int(pulse_size * 3), int(pulse_size * 3)), pygame.SRCALPHA)
                warning_center = int(pulse_size * 1.5)
                self._draw_hexagon(warning_surf, warning_center, warning_center, 
                                 pulse_size * 1.3, (255, 100, 100, warning_alpha), hex_rotation)
                surface.blit(warning_surf, (x - warning_center, y - warning_center))

        # Floating texts
        for text_obj in self.floating_texts:
            alpha_factor = text_obj['life'] / text_obj['max_life']
            scale = text_obj['scale']

            if "WAVE" in text_obj['text'] or "LEVEL" in text_obj['text'] or "GAME OVER" in text_obj['text']:
                font = self.font_big
            elif any(keyword in text_obj['text'] for keyword in ["COMBO", "BONUS", "PERFECT", "AMAZING", "INCREDIBLE"]):
                font = self.font_medium
            else:
                font = self.font_small

            text_surf = font.render(text_obj['text'], True, text_obj['color'])

            new_w = int(text_surf.get_width() * scale)
            new_h = int(text_surf.get_height() * scale)

            if new_w > 0 and new_h > 0:
                text_surf = pygame.transform.scale(text_surf, (new_w, new_h))
                text_surf.set_alpha(int(255 * alpha_factor))

                x = int(text_obj['x'] - new_w // 2)
                y = int(text_obj['y'] - new_h // 2)

                # Outline
                outline = font.render(text_obj['text'], True, (0, 0, 0))
                outline = pygame.transform.scale(outline, (new_w, new_h))
                outline.set_alpha(int(220 * alpha_factor))
                for ox, oy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
                    surface.blit(outline, (x + ox, y + oy))

                surface.blit(text_surf, (x, y))

        # HUD
        self._draw_minimal_hud(surface)

        # Bullet time
        if self.time_slow < 1.0:
            bt_overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
            bt_overlay.fill((100, 100, 255, 30))
            surface.blit(bt_overlay, (0, 0))

            bt_text = self.font_medium.render("BULLET TIME", True, (180, 180, 255))
            bt_text.set_alpha(int((math.sin(self.time * 10) * 0.5 + 0.5) * 200 + 55))
            surface.blit(bt_text, (640 - bt_text.get_width() // 2, 650))

        # Flash
        if self.flash_timer > 0:
            flash_surf = pygame.Surface((1280, 720), pygame.SRCALPHA)
            flash_surf.fill((255, 80, 80, int(100 * self.flash_timer)))
            surface.blit(flash_surf, (0, 0))

        if self.game_over:
            self._draw_game_over(surface)

        # === MENU PAUSA - AGGIUNGI QUI ===
        if hasattr(self, 'paused') and self.paused and self.confirmexit:
            self._draw_pause_menu(surface)
        # === FINE PAUSA ===














    def _draw_minimal_hud(self, surface: pygame.Surface):
        hud_surf = pygame.Surface((1280, 720), pygame.SRCALPHA)

        # Score
        score_surf = self.font_medium.render(f"{self.score}", True, (255, 255, 220))
        hud_surf.blit(score_surf, (18, 12))

        # Lives
        for i in range(self.lives):
            heart_x = 18 + i * 32
            self._draw_mini_heart(hud_surf, heart_x, 55, (255, 120, 180), 11)

        # Level/Wave
        level_surf = self.font_small.render(f"L{self.level}", True, (180, 255, 180))
        hud_surf.blit(level_surf, (1230, 14))

        wave_surf = self.font_tiny.render(f"W{self.wave}", True, (180, 220, 255))
        hud_surf.blit(wave_surf, (1230, 42))

        # Combo
        if self.combo > 1:
            combo_text = f"x{self.combo}"
            combo_col = self._get_combo_color()
            combo_surf = self.font_medium.render(combo_text, True, combo_col)

            timer_ratio = self.combo_timer / 4.0
            bar_w = 100
            bar_x = 640 - bar_w // 2

            pygame.draw.rect(hud_surf, (0, 0, 0, 120), (bar_x, 50, bar_w, 5))
            fill_w = int(bar_w * timer_ratio)
            pygame.draw.rect(hud_surf, (*combo_col, 200), (bar_x, 50, fill_w, 5))

            hud_surf.blit(combo_surf, (640 - combo_surf.get_width() // 2, 12))

        # Power-ups
        pu_y = 680
        pu_list = []

        if self.shield_active:
            pu_list.append((f"SHIELD {self.shield_power}", (120, 220, 255)))
        if self.multishot_ammo > 0:
            pu_list.append((f"TRIPLE {self.multishot_ammo}", (255, 180, 100)))
        if self.pierce_ammo > 0:
            pu_list.append((f"PIERCE {self.pierce_ammo}", (180, 100, 255)))
        if self.shotgun_ammo > 0:
            pu_list.append((f"SHOTGUN {self.shotgun_ammo}", (255, 220, 80)))
        if self.uzi_ammo > 0:
            pu_list.append((f"AUTO {self.uzi_ammo}", (80, 255, 220)))

        for text, color in pu_list:
            pu_surf = self.font_small.render(text, True, color)
            hud_surf.blit(pu_surf, (18, pu_y))
            pu_y -= 26

        surface.blit(hud_surf, (0, 0))

    def _draw_mini_heart(self, surface: pygame.Surface, x: int, y: int, color: Tuple[int, int, int], size: int):
        points = [
            (x, y + size // 3),
            (x - size, y - size // 2),
            (x - size // 2, y - size),
            (x, y - size // 2),
            (x + size // 2, y - size),
            (x + size, y - size // 2),
            (x, y + size // 3)
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, (255, 255, 255), points, 1)

        shine_x = x - size // 3
        shine_y = y - size // 2
        pygame.draw.circle(surface, (255, 255, 255), (shine_x, shine_y), 3)

    def _draw_game_over(self, surface: pygame.Surface):
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        surface.blit(overlay, (0, 0))

        go_surf = self.font_huge.render("GAME OVER", True, (255, 100, 100))
        for offset in [(-3, -3), (3, -3), (-3, 3), (3, 3)]:
            shadow = self.font_huge.render("GAME OVER", True, (100, 0, 0))
            surface.blit(shadow, (640 - shadow.get_width() // 2 + offset[0], 160 + offset[1]))
        surface.blit(go_surf, (640 - go_surf.get_width() // 2, 160))

        stats = [
            f"Final Score: {self.score}",
            f"Max Combo: x{self.combo_max}",
            f"Level {self.level} - Wave {self.wave}",
            f"Accuracy: {self.accuracy}%"
        ]

        y = 320
        for stat in stats:
            stat_surf = self.font_small.render(stat, True, (220, 255, 220))
            surface.blit(stat_surf, (640 - stat_surf.get_width() // 2, y))
            y += 40

        hint_pulse = abs(math.sin(self.time * 4)) * 0.5 + 0.5
        hint_col = tuple(int(c * hint_pulse + (1 - hint_pulse) * 100) for c in (255, 255, 180))
        hint_surf = self.font_small.render("RIGHT CLICK TO CONTINUE", True, hint_col)
        surface.blit(hint_surf, (640 - hint_surf.get_width() // 2, 570))







    def _draw_pause_menu(self, surface: pygame.Surface):
        """Menu pausa IDENTICO a Missile Commander [file:1]"""
        # Overlay identico
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # PAUSED titolo (y=150, font 80px)
        pausefont = pygame.font.Font(None, 80)  # Come fontpause
        pausetext = pausefont.render("PAUSED", True, (255, 255, 255))
        surface.blit(pausetext, (640 - pausetext.get_width() // 2, 150))
        
        # Stats panel (y=280, spacing 40px, font 26px)
        statsfont = pygame.font.Font(None, 26)  # Come fontcombo
        stats = [
            f"Score: {self.score}",
            f"Level: {self.level}/{self.level}",  # Adatta ai tuoi dati
            f"Max Combo: {self.combo_max}",
            f"Bricks: {getattr(self, 'total_bricks_broken', 0)}",  # O altra stat
            f"Powerups: {getattr(self, 'power_ups_collected', 0)}"  # O altra stat
        ]
        y = 280
        for stat in stats:
            stattext = statsfont.render(stat, True, (255, 255, 255))
            surface.blit(stattext, (640 - stattext.get_width() // 2, y))
            y += 40
        
        # Buttons (font 32px, y=550/600)
        btnfont = pygame.font.Font(None, 32)  # Come fontlevel
        
        exittext = btnfont.render("LEFT CLICK - Exit", True, (255, 100, 100))
        continuetext = btnfont.render("RIGHT CLICK - Continue", True, (100, 255, 100))
        
        surface.blit(exittext, (640 - exittext.get_width() // 2, 550))
        surface.blit(continuetext, (640 - continuetext.get_width() // 2, 600))












# ============== GAME MANAGER ==============
class GameManager:
    def __init__(self):
        pygame.init()
        
        # Core systems
        self.config = Config()
        self.display = DisplayManager(self.config)
        self.spinner = SpinnerInput(self.config)
        self.synth = SoundSynthesizer()
        self.high_score_mgr = HighScoreManager()
        self.music_player = MusicPlayer()
        self.clock = pygame.time.Clock()
        
        # Game instances - inizializzati lazy
        self._game_instances = None
        
        # State management
        self.states: Dict[str, GameState] = {}
        self.current_state = None
        
        # Performance tracking
        self.frame_times = []
        self.max_frame_samples = 60
        
        # Initialize
        self._initialize_base_states()
        self._change_state("main_menu")
    
    @property
    def games(self) -> List[MiniGame]:
        """Lazy loading dei giochi"""
        if self._game_instances is None:
            self._game_instances = [
                BreakoutSpinner(self.synth),
                MissileCommander(self.synth),
                SpinnerDefense(self.synth),
                PongSpinner(self.synth),
                Kaleidoscope(self.synth),
                SpinDuel(self.synth),
                YahtzeeSpinner(self.synth)
            ]
        return self._game_instances
    
    def _initialize_base_states(self):
        """Inizializza solo gli stati essenziali"""
        # Main menu e config sempre disponibili
        self.states["main_menu"] = MainMenuState(self.games, self.high_score_mgr, self.synth)
        self.states["config"] = ConfigMenuState(self.config, self.display, self.synth)
    
    def _get_or_create_game_state(self, game_index: int) -> PlayingState:
        """Lazy creation degli stati di gioco"""
        state_key = f"game:{game_index}"
        if state_key not in self.states:
            if 0 <= game_index < len(self.games):
                self.states[state_key] = PlayingState(
                    self.games[game_index], 
                    self.high_score_mgr, 
                    self.synth
                )
            else:
                raise ValueError(f"Invalid game index: {game_index}")
        return self.states[state_key]
    
    def _get_or_create_high_score_state(self, game_name: str) -> HighScoreState:
        """Lazy creation degli stati high score"""
        state_key = f"view_scores:{game_name}"
        if state_key not in self.states:
            self.states[state_key] = HighScoreState(
                game_name, 
                self.high_score_mgr, 
                self.synth
            )
        return self.states[state_key]
    
    def _get_or_create_name_entry_state(self, game_name: str, score: int) -> NameEntryState:
        """Lazy creation degli stati name entry"""
        state_key = f"name_entry:{game_name}:{score}"
        if state_key not in self.states:
            self.states[state_key] = NameEntryState(game_name, score, self.synth)
        return self.states[state_key]
    
    def _change_state(self, state_name: str):
        """Gestione transizioni di stato con parsing migliorato"""
        try:
            # Parse state name
            if state_name.startswith("game:"):
                game_index = int(state_name.split(":", 1)[1])
                next_state = self._get_or_create_game_state(game_index)
            
            elif state_name.startswith("view_scores:"):
                game_name = state_name.split(":", 1)[1]
                next_state = self._get_or_create_high_score_state(game_name)
            
            elif state_name.startswith("name_entry:"):
                parts = state_name.split(":", 2)
                game_name = parts[1]
                score = int(parts[2])
                next_state = self._get_or_create_name_entry_state(game_name, score)
            
            elif state_name.startswith("save_score:"):
                parts = state_name.split(":", 3)
                game_name = parts[1]
                score = int(parts[2])
                player_name = parts[3]
                self.high_score_mgr.save_score(game_name, score, player_name)
                # Redirect to high scores
                return self._change_state(f"view_scores:{game_name}")
            
            elif state_name in self.states:
                next_state = self.states[state_name]
            
            else:
                print(f"Warning: Unknown state '{state_name}', returning to main menu")
                next_state = self.states["main_menu"]
            
            # Perform transition
            if self.current_state:
                self.current_state.on_exit()
            
            self.current_state = next_state
            self.current_state.on_enter()
            
        except (ValueError, IndexError, KeyError) as e:
            print(f"Error changing state to '{state_name}': {e}")
            # Fallback to main menu
            if self.current_state:
                self.current_state.on_exit()
            self.current_state = self.states["main_menu"]
            self.current_state.on_enter()
    
    def _cleanup_unused_states(self):
        """Rimuove stati inutilizzati per liberare memoria"""
        # Mantieni solo: main_menu, config, current_state
        essential_states = {"main_menu", "config"}
        if self.current_state:
            current_key = next(
                (k for k, v in self.states.items() if v == self.current_state), 
                None
            )
            if current_key:
                essential_states.add(current_key)
        
        # Rimuovi stati temporanei (name_entry, vecchi view_scores)
        keys_to_remove = [
            k for k in self.states.keys() 
            if k not in essential_states and (
                k.startswith("name_entry:") or 
                k.startswith("view_scores:")
            )
        ]
        
        for key in keys_to_remove:
            del self.states[key]
    
    def _track_performance(self, dt: float):
        """Traccia performance per debug"""
        self.frame_times.append(dt)
        if len(self.frame_times) > self.max_frame_samples:
            self.frame_times.pop(0)
    
    def get_average_fps(self) -> float:
        """Calcola FPS medio"""
        if not self.frame_times:
            return 60.0
        avg_dt = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_dt if avg_dt > 0 else 60.0
    
    def run(self):
        """Main game loop ottimizzato"""
        # Avvia musica
        self.music_player.start()
        
        running = True
        frame_count = 0
        cleanup_interval = 600  # Cleanup ogni 10 secondi (60fps * 10)
        
        try:
            while running:
                # Delta time con cap per evitare spike
                dt = min(self.clock.tick(60) / 1000.0, 0.1)  # Max 100ms
                frame_count += 1
                
                # Track performance (opzionale, commentare in produzione)
                # self._track_performance(dt)
                
                # Event handling
                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        running = False
                        break
                    
                    # Music player events
                    self.music_player.handle_event(event)
                    
                    # Emergency exit: ESC key
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        if self.current_state == self.states.get("main_menu"):
                            running = False
                        else:
                            self._change_state("main_menu")
                
                # Input update
                self.spinner.update(events)
                spinner_delta = self.spinner.get_rotation_delta()
                
                # State update
                if self.current_state:
                    try:
                        next_state = self.current_state.update(dt, spinner_delta, self.spinner)
                        
                        if next_state == "exit":
                            running = False
                        elif next_state:
                            self._change_state(next_state)
                    
                    except Exception as e:
                        print(f"Error in state update: {e}")
                        # Fallback to main menu on error
                        self._change_state("main_menu")
                
                # Rendering
                try:
                    if self.current_state:
                        self.current_state.draw(self.display.get_virtual_surface())
                    self.display.render()
                
                except Exception as e:
                    print(f"Error in rendering: {e}")
                
                # Periodic cleanup
                if frame_count % cleanup_interval == 0:
                    self._cleanup_unused_states()
        
        except KeyboardInterrupt:
            print("\nGame interrupted by user")
        
        except Exception as e:
            print(f"Fatal error in game loop: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Cleanup
            self._shutdown()
    
    def _shutdown(self):
        """Cleanup resources"""
        print("Shutting down...")
        
        # Stop music
        try:
            self.music_player.stop()
        except:
            pass
        
        # Release input
        try:
            self.spinner.release()
        except:
            pass
        
        # Quit pygame
        try:
            pygame.quit()
        except:
            pass
        
        print("Shutdown complete")
        sys.exit()







class MusicPlayer:
    """Gestisce la riproduzione continua della playlist"""
    MUSIC_END = pygame.USEREVENT + 10
    
    def __init__(self):
        self.music_folder = Path(resource_path("music"))
        self.playlist = []
        self.current_index = 0
        self.enabled = False
        self.load_playlist()
    
    def load_playlist(self):
        """Carica tutti i file MP3 dalla cartella music"""
        if not self.music_folder.exists():
            self.music_folder.mkdir(exist_ok=True)
            print(f"Cartella {self.music_folder} creata.")
            return
        
        self.playlist = sorted([str(f) for f in self.music_folder.glob("*.mp3")])
        
        if self.playlist:
            print(f"♪ Trovate {len(self.playlist)} canzoni")
        else:
            print(f"Nessun MP3 in {self.music_folder}")
    
    def start(self):
        """Avvia la riproduzione della playlist"""
        if not self.playlist:
            print("⚠ Playlist vuota, musica non avviata")
            return
        
        try:
            pygame.mixer.music.set_endevent(self.MUSIC_END)
            self.current_index = 0
            self.play_current()
            self.enabled = True
            print("✓ MusicPlayer avviato")
        except Exception as e:
            print(f"✗ Errore avvio: {e}")
    
    def play_current(self):
        """Riproduce la canzone corrente"""
        if not self.playlist:
            return
        
        try:
            song_path = self.playlist[self.current_index]
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.set_volume(0.4)  # Volume 0.0 - 1.0
            pygame.mixer.music.play()
            print(f"♪ {Path(song_path).name}")
        except pygame.error as e:
            print(f"✗ Errore: {e}")
            self.next_song()
    
    def next_song(self):
        """Passa alla canzone successiva (loop infinito)"""
        if not self.playlist:
            return
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.play_current()
    
    def handle_event(self, event):
        """Gestisce l'evento di fine canzone"""
        if self.enabled and event.type == self.MUSIC_END:
            self.next_song()




# ============== START ==============

if __name__ == "__main__":
    try:
        game = GameManager()
        game.run()
    except Exception as e:
        print(f"Failed to start game: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
