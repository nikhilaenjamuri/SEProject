$(document).ready(function () {
    let pdfPaths = [];

    // Show alert message
    function showAlert(message, type) {
        $('#alert-message').text(message).removeClass().addClass(`alert alert-${type}`).fadeIn();
        setTimeout(function () {
            $('#alert-message').fadeOut();
        }, 3000);
    }

    // Upload Template
    $('#upload-template').on('click', function () {
        const templateFile = $('#template-file')[0].files[0];
        if (templateFile) {
            const formData = new FormData();
            formData.append('file', templateFile);

            $.ajax({
                url: '/upload_template',
                type: 'POST',
                data: formData,
                contentType: false,
                processData: false,
                success: function (response) {
                    showAlert('Template uploaded successfully!', 'success');
                },
                error: function () {
                    showAlert('Error uploading template.', 'error');
                }
            });
        } else {
            showAlert('Please select a template file to upload.', 'error');
        }
    });

    // Upload Data
    $('#upload-data').on('click', function () {
        const dataFile = $('#data-file')[0].files[0];
        if (dataFile) {
            const formData = new FormData();
            formData.append('file', dataFile);

            $.ajax({
                url: '/upload_data',
                type: 'POST',
                data: formData,
                contentType: false,
                processData: false,
                success: function (response) {
                    showAlert('Data uploaded successfully!', 'success');
                },
                error: function () {
                    showAlert('Error uploading data.', 'error');
                }
            });
        } else {
            showAlert('Please select a data file to upload.', 'error');
        }
    });

    // Generate PDFs
    $('#generate-pdfs').on('click', function () {
        const templateName = $('#template-name').val();
        const dataFileName = $('#data-file-name').val();

        if (templateName && dataFileName) {
            $.ajax({
                url: '/generate_pdfs',
                type: 'POST',
                data: {
                    template_name: templateName,
                    data_file_name: dataFileName
                },
                success: function (response) {
                    if (response.pdf_paths) {
                        pdfPaths = response.pdf_paths;
                        $('#send-emails').prop('disabled', false);  // Enable the Send Emails button
                        showAlert('PDFs generated successfully!', 'success');
                    } else {
                        showAlert('Error generating PDFs.', 'error');
                    }
                },
                error: function () {
                    showAlert('Error generating PDFs.', 'error');
                }
            });
        } else {
            showAlert('Please provide both template and data file names.', 'error');
        }
    });

    // Send Emails
    $('#send-emails').on('click', function () {
        if (pdfPaths.length > 0) {
            $.ajax({
                url: '/send_emails',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ pdf_paths: pdfPaths, data_file_name: $('#data-file-name').val() }),
                success: function (response) {
                    showAlert('Emails sent successfully!', 'success');
                    pdfPaths = [];  // Clear the pdf paths
                    $('#send-emails').prop('disabled', true);  // Disable the Send Emails button
                },
                error: function () {
                    showAlert('Error sending emails.', 'error');
                }
            });
        } else {
            showAlert('No PDFs generated. Please generate PDFs first.', 'error');
        }
    });
});
