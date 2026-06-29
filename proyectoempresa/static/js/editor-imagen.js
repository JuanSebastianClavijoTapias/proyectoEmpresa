/**
 * editor-imagen.js — Canvas de dibujo para anotar/resaltar imágenes
 * Funcionalidad: tomar foto → dibujar con lápiz → guardar imagen anotada
 * También: botón "Anotar" en galería de imágenes existentes
 *
 * Uso:
 *   EditorImagen.abrirEditor(fileOrUrl, onSaveCallback)
 *   - fileOrUrl: File (blob) de captura, o string URL de imagen existente
 *   - onSaveCallback: function(blob, filename) — llamado al guardar
 */

var EditorImagen = (function() {
    'use strict';

    var COLORS = ['#e74c3c', '#f39c12', '#2ecc71', '#3498db', '#8e44ad', '#34495e', '#ffffff', '#000000'];
    var DEFAULT_COLOR = '#e74c3c';
    var DEFAULT_WIDTH = 4;

    var _modal = null;
    var _canvas = null;
    var _ctx = null;
    var _img = null;
    var _drawing = false;
    var _hasDrawed = false;
    var _currentColor = DEFAULT_COLOR;
    var _currentWidth = DEFAULT_WIDTH;
    var _undoStack = [];
    var _onSave = null;

    function _createModal() {
        if (_modal) return;
        _modal = document.createElement('div');
        _modal.id = 'editor-imagen-modal';
        _modal.innerHTML = `
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); display: flex; flex-direction: column; z-index: 99999;">
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #2c3e50; color: white; flex-shrink: 0;">
                    <span style="font-weight: 600; font-size: 16px;"><i class="bi bi-pencil"></i> Resaltar imagen</span>
                    <div style="display: flex; gap: 8px;">
                        <button id="eim-cancel" class="btn btn-sm btn-outline-light"><i class="bi bi-x-lg"></i> Cancelar</button>
                        <button id="eim-save" class="btn btn-sm" style="background: linear-gradient(135deg, #27ae60, #229954); color: white; border: none;"><i class="bi bi-check-lg"></i> Guardar</button>
                    </div>
                </div>
                <div style="flex: 1; overflow: auto; display: flex; align-items: center; justify-content: center; position: relative;">
                    <canvas id="eim-canvas" style="max-width: 100%; max-height: 100%; cursor: crosshair; touch-action: none;"></canvas>
                </div>
                <div style="display: flex; align-items: center; gap: 8px; padding: 10px 12px; background: #34495e; color: white; flex-wrap: wrap; flex-shrink: 0;">
                    <div style="display: flex; gap: 4px; align-items: center;" id="eim-colors"></div>
                    <div style="width: 1px; height: 28px; background: rgba(255,255,255,0.3); margin: 0 4px;"></div>
                    <label style="font-size: 12px; margin: 0;">
                        <i class="bi bi-brush"></i>
                        <input type="range" id="eim-width" min="1" max="20" value="${DEFAULT_WIDTH}" style="width: 80px; vertical-align: middle;">
                    </label>
                    <button id="eim-undo" class="btn btn-sm btn-outline-light" title="Deshacer"><i class="bi bi-arrow-counterclockwise"></i></button>
                    <button id="eim-clear" class="btn btn-sm btn-outline-light" title="Limpiar todo"><i class="bi bi-eraser"></i></button>
                </div>
            </div>
        `;
        document.body.appendChild(_modal);

        _canvas = _modal.querySelector('#eim-canvas');
        _ctx = _canvas.getContext('2d');

        var colorsDiv = _modal.querySelector('#eim-colors');
        COLORS.forEach(function(color) {
            var dot = document.createElement('span');
            dot.style.cssText = 'display:inline-block;width:24px;height:24px;border-radius:50%;background:' + color + ';cursor:pointer;border:2px solid ' + (color === _currentColor ? '#fff' : 'transparent') + ';';
            dot.dataset.color = color;
            dot.addEventListener('click', function() {
                _currentColor = color;
                colorsDiv.querySelectorAll('span').forEach(function(s) {
                    s.style.borderColor = (s.dataset.color === color) ? '#fff' : 'transparent';
                });
            });
            colorsDiv.appendChild(dot);
        });

        _modal.querySelector('#eim-width').addEventListener('input', function() {
            _currentWidth = parseInt(this.value);
        });

        _modal.querySelector('#eim-undo').addEventListener('click', _undo);
        _modal.querySelector('#eim-clear').addEventListener('click', _clear);
        _modal.querySelector('#eim-cancel').addEventListener('click', _close);
        _modal.querySelector('#eim-save').addEventListener('click', _save);

        _canvas.addEventListener('mousedown', _startDraw);
        _canvas.addEventListener('mousemove', _draw);
        _canvas.addEventListener('mouseup', _stopDraw)
        _canvas.addEventListener('mouseleave', _stopDraw);
        _canvas.addEventListener('touchstart', _touchStart, { passive: false });
        _canvas.addEventListener('touchmove', _touchMove, { passive: false });
        _canvas.addEventListener('touchend', _stopDraw);
    }

    function _getPos(e) {
        var rect = _canvas.getBoundingClientRect();
        var scaleX = _canvas.width / rect.width;
        var scaleY = _canvas.height / rect.height;
        return {
            x: (e.clientX - rect.left) * scaleX,
            y: (e.clientY - rect.top) * scaleY
        };
    }

    function _pushUndo() {
        _undoStack.push(_ctx.getImageData(0, 0, _canvas.width, _canvas.height));
        if (_undoStack.length > 30) _undoStack.shift();
    }

    function _undo() {
        if (_undoStack.length === 0) return;
        var data = _undoStack.pop();
        _ctx.putImageData(data, 0, 0);
        var canvasData = _ctx.getImageData(0, 0, _canvas.width, _canvas.height);
        var pixels = canvasData.data;
        var hasNonEmpty = false;
        for (var i = 3; i < pixels.length; i += 4) {
            if (pixels[i] > 0) { hasNonEmpty = true; break; }
        }
        _hasDrawed = _undoStack.length > 0 || hasNonEmpty;
    }

    function _clear() {
        _pushUndo();
        _ctx.clearRect(0, 0, _canvas.width, _canvas.height);
        if (_img) _ctx.drawImage(_img, 0, 0);
        _hasDrawed = false;
    }

    function _startDraw(e) {
        _drawing = true;
        _pushUndo();
        var pos = _getPos(e);
        _ctx.beginPath();
        _ctx.moveTo(pos.x, pos.y);
    }

    function _draw(e) {
        if (!_drawing) return;
        var pos = _getPos(e);
        _ctx.lineTo(pos.x, pos.y);
        _ctx.strokeStyle = _currentColor;
        _ctx.lineWidth = _currentWidth;
        _ctx.lineCap = 'round';
        _ctx.lineJoin = 'round';
        _ctx.stroke();
        _hasDrawed = true;
    }

    function _stopDraw() {
        if (_drawing) {
            _drawing = false;
            _ctx.closePath();
        }
    }

    function _touchStart(e) {
        e.preventDefault();
        var touch = e.touches[0];
        var mouseEvent = new MouseEvent('mousedown', { clientX: touch.clientX, clientY: touch.clientY });
        _canvas.dispatchEvent(mouseEvent);
    }

    function _touchMove(e) {
        e.preventDefault();
        var touch = e.touches[0];
        var mouseEvent = new MouseEvent('mousemove', { clientX: touch.clientX, clientY: touch.clientY });
        _canvas.dispatchEvent(mouseEvent);
    }

    function _save() {
        _canvas.toBlob(function(blob) {
            if (_onSave) {
                var filename = _hasDrawed ? 'anotada_' + Date.now() + '.jpg' : 'original_' + Date.now() + '.jpg';
                _onSave(blob, filename, _hasDrawed);
            }
            _close();
        }, 'image/jpeg', 0.85);
    }

    function _close() {
        if (_modal) {
            _modal.remove();
            _modal = null;
            _canvas = null;
            _ctx = null;
            _onSave = null;
            _undoStack = [];
            _hasDrawed = false;
            _drawing = false;
        }
    }

    function abrirEditor(source, onSaveCallback) {
        _createModal();
        _onSave = onSaveCallback;

        _img = new Image();
        _img.onload = function() {
            var maxW = window.innerWidth * 0.95;
            var maxH = window.innerHeight * 0.65;
            var ratio = Math.min(maxW / _img.width, maxH / _img.height, 1);
            _canvas.width = _img.width * ratio;
            _canvas.height = _img.height * ratio;
            _ctx.clearRect(0, 0, _canvas.width, _canvas.height);
            _ctx.drawImage(_img, 0, 0, _canvas.width, _canvas.height);
            _pushUndo();
        };

        if (typeof source === 'string') {
            _img.src = source;
        } else if (source instanceof File || source instanceof Blob) {
            _img.src = URL.createObjectURL(source);
        }
    }

    return {
        abrirEditor: abrirEditor,
        close: _close,
    };

})();
