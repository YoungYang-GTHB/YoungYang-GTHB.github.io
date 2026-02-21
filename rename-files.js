const fs = require('fs');
const path = require('path');

const dir = path.join(__dirname, 'public', 'projects', 'tcm-therapy', 'smart-gourd');

console.log('Reading directory:', dir);

// 读取目录中的所有文件
const files = fs.readdirSync(dir);
console.log('Found files:', files);

// 重命名映射
const renameMap = {
  '第一代 - 智能葫芦灸理疗仪 - 实物照片.jpg': 'gen1-product-photo.jpg',
  '第一代 - 智能葫芦灸理疗仪视频介绍.mp4': 'gen1-product-video.mp4',
};

// 执行重命名
files.forEach(file => {
  if (renameMap[file]) {
    const oldPath = path.join(dir, file);
    const newPath = path.join(dir, renameMap[file]);
    fs.renameSync(oldPath, newPath);
    console.log(`Renamed: ${file} -> ${renameMap[file]}`);
  }
});

console.log('Done!');
