<?php

// require_once __DIR__ . '/vendor/autoload.php';
// use Box\Spout\Reader\Common\Creator\ReaderEntityFactory;

// // $path = __DIR__ . '/uploads/rekap winner internus.xlsx';
// var_dump($_FILES['excel_file']);
// die;

// # array to save data read
// $data = [];
// # boolean to see if first row has been read (skip column title row)
// $isFirstRowFound = false;

// # open the file
// $reader = ReaderEntityFactory::createXLSXReader();
// $reader->open($path);
// # read each cell of each row of each sheet
// foreach ($reader->getSheetIterator() as $sheet) {
//     foreach ($sheet->getRowIterator() as $row) {
//         if(!$isFirstRowFound) {
//             $isFirstRowFound = true;
//             continue;
//         }
//         $rowData = [];
//         foreach ($row->getCells() as $cell) {
//             $rowData[] = $cell->getValue();
//         }
//         $data[] = $rowData;
//     }
// }
// $reader->close();


// return $data;

?>