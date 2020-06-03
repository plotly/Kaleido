function exportFromSpec(spec) {
    return Plotly.toImage(spec.figure, {
        format: spec.format || 'png',
        scale: spec.scale || 1.0,
        width: spec.width || 700,
        height: spec.height || 450
    });
}
