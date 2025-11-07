#!/usr/bin/env node

/**
 * Convert SVG favicon to PNG for better compatibility with messaging apps
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import sharp from 'sharp';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, '..');
const publicDir = path.join(projectRoot, 'public');
const svgPath = path.join(publicDir, 'favicon.svg');

// Sizes to generate (for different use cases)
const sizes = [
  { size: 512, name: 'favicon-512.png', description: 'OG image for messaging apps' },
  { size: 1200, name: 'og-image.png', description: 'Large OG image for social media' },
  { size: 180, name: 'apple-touch-icon.png', description: 'Apple touch icon' }
];

async function convertFavicon() {
  console.log('📸 Converting SVG favicon to PNG formats...\n');

  if (!fs.existsSync(svgPath)) {
    console.error(`❌ Error: ${svgPath} not found!`);
    process.exit(1);
  }

  try {
    const svgBuffer = fs.readFileSync(svgPath);
    
    for (const { size, name, description } of sizes) {
      const outputPath = path.join(publicDir, name);
      
      await sharp(svgBuffer)
        .resize(size, size, {
          fit: 'contain',
          background: { r: 0, g: 0, b: 0, alpha: 0 } // Transparent background
        })
        .png()
        .toFile(outputPath);
      
      console.log(`✅ Created ${name} (${size}x${size}) - ${description}`);
    }
    
    console.log('\n🎉 All PNG favicons created successfully!');
    console.log('\nNext steps:');
    console.log('1. Update index.html to use PNG for og:image if needed');
    console.log('2. Redeploy the frontend');
    
  } catch (error) {
    console.error('❌ Error converting favicon:', error.message);
    console.error('\nIf sharp is not installed, run: npm install');
    process.exit(1);
  }
}

convertFavicon();
