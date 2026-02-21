const fs = require('fs');
const path = require('path');

const dir = path.join(__dirname, 'public', 'projects', 'tcm-therapy', 'smart-gourd');

console.log('Directory:', dir);

// 读取目录
const files = fs.readdirSync(dir);
console.log('Files:', files);

// 重命名包含中文的文件
files.forEach((file, index) => {
  // 检查是否包含非 ASCII 字符
  if (/[^\x00-\x7F]/.test(file)) {
    const ext = path.extname(file);
    const newName = `gen1-file-${index + 1}${ext}`;
    const oldPath = path.join(dir, file);
    const newPath = path.join(dir, newName);
    
    try {
      fs.renameSync(oldPath, newPath);
      console.log(`Renamed: ${file} -> ${newName}`);
    } catch (e) {
      console.error(`Failed to rename ${file}:`, e.code, e.message);
      // 尝试使用短文件名
      console.log('Trying alternative method...');
    }
  }
});

// 验证结果
const finalFiles = fs.readdirSync(dir);
console.log('Final files:', finalFiles);
